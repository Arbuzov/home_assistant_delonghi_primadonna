"""Delongi primadonna device description"""
import asyncio
import copy

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - fallback for older Home Assistant
    from homeassistant.backports.enum import StrEnum

import logging
import time
import uuid
from binascii import crc_hqx, hexlify
from dataclasses import dataclass
from datetime import datetime
from enum import IntFlag

from bleak.exc import BleakDBusError, BleakError
from bleak_retry_connector import (BleakClientWithServiceCache,
                                   establish_connection)
from homeassistant.components import bluetooth
from homeassistant.const import CONF_MAC, CONF_MODEL, CONF_NAME
from homeassistant.core import HomeAssistant

from .const import (AMERICANO_OFF, AMERICANO_ON, AVAILABLE_PROFILES,
                    BASE_COMMAND, BEVERAGE_NONE, BYTES_AUTOPOWEROFF_COMMAND,
                    BYTES_LOAD_PROFILES, BYTES_LOAD_SWITCHES, BYTES_POWER,
                    BYTES_POWER_OFF, BYTES_STATISTICS_COMMAND,
                    BYTES_SWITCH_COMMAND, BYTES_TIME_COMMAND,
                    BYTES_WATER_HARDNESS_COMMAND,
                    BYTES_WATER_TEMPERATURE_COMMAND, COFFE_OFF, COFFE_ON,
                    COFFEE_GROUNDS_CONTAINER_CLEAN,
                    COFFEE_GROUNDS_CONTAINER_DETACHED,
                    COFFEE_GROUNDS_CONTAINER_FULL, COMMAND_NAMES,
                    CONTROLL_CHARACTERISTIC, DEBUG, DEFAULT_DEVICE_NAME,
                    DEFAULT_IMAGE_URL, DEVICE_READY, DEVICE_STATUS,
                    DEVICE_TURNOFF, DOMAIN, DOPPIO_OFF, DOPPIO_ON,
                    ESPRESSO2_OFF, ESPRESSO2_ON, ESPRESSO_OFF, ESPRESSO_ON,
                    HOTWATER_OFF, HOTWATER_ON, LONG_OFF, LONG_ON,
                    MACHINE_STATUS, NAME_CHARACTERISTIC, NOZZLE_STATE,
                    PARAM_SWITCHES, START_COFFEE, STEAM_OFF, STEAM_ON,
                    SWITCH_BIT_CUP_LIGHT, SWITCH_BIT_ENERGY_SAVE,
                    SWITCH_BIT_SOUNDS, WATER_SHORTAGE, WATER_TANK_DETACHED)
from .machine_switch import MachineSwitch, parse_switches
from .model import get_machine_model

_LOGGER = logging.getLogger(__name__)

START_BYTE = 0xD0


@dataclass
class MonitorData:
    """Monitor Data structure"""
    switches: int
    alarms: int
    status: int
    sub_status: int
    nozzle_state: int
    percentage: int = 0


def describe_command(message) -> str:
    """Name a command for log messages, falling back to its type byte."""
    if len(message) < 3:
        return 'unknown'
    return COMMAND_NAMES.get(message[2], f'0x{message[2]:02x}')


def parse_monitor_data(data: bytes) -> MonitorData | None:
    """Parse Monitor Data packet (v1 0x70 or v2 0x75)"""
    if len(data) < 3:
        return None

    answer_id = data[2]

    # Defaults
    switches = 0
    alarms = 0
    status = 0
    sub_status = 0
    nozzle_state = -1
    percentage = 0

    if answer_id == 0x75:  # MonitorDataV2
        if len(data) < 14:
            return None
        # Switches: Bytes 5, 6 (Little Endian)
        switches = data[5] + (data[6] << 8)

        # Alarms: Bytes 7, 8, 12, 13 (Little Endian in blocks)
        # Based on MonitorDataV2.b():
        # iS = z.S(bArr[7]) + (z.S(bArr[8]) << 8) + (z.S(bArr[12]) << 16) + \
        # (z.S(bArr[13]) << 24)
        alarms = (data[7]
                  + (data[8] << 8)
                  + (data[12] << 16)
                  + (data[13] << 24))

        # Status/State: Byte 9
        status = data[9]

        # SubStatus: Byte 10
        sub_status = data[10]

        # Nozzle State: Byte 4 (from MonitorDataV2.a())
        nozzle_state = data[4]

        # Dispensing progress: byte 11 carries the percentage
        # (see longshot MonitorV2Response)
        percentage = data[11]

    elif answer_id == 0x70:  # MonitorData (v1)
        if len(data) < 11:
            return None

        # Switches: Bytes 9, 10
        # Based on MonitorData.g(): bArr[9] + (bArr[10] << 8)
        switches = data[9] + (data[10] << 8)

        # Alarms: Bytes 4, 5
        # Based on MonitorData.b(): bArr[4] + (bArr[5] << 8)
        alarms = data[4] + (data[5] << 8)

        # Status/State: Byte 8
        # Based on MonitorData.f(): bArr[8]
        status = data[8]

        # SubStatus: Byte 9
        # Based on MonitorData.e(): bArr[9]
        # Note: Byte 9 is also used for switches low byte?
        # MonitorData.g (Switches) uses 9, 10.
        # MonitorData.e (SubState/Aux) uses 9.
        # We will extract it as sub_status anyway.
        sub_status = data[9]

        # Nozzle State: a() returns -1 for v1.
        nozzle_state = -1

    else:
        return None

    return MonitorData(
        switches, alarms, status, sub_status, nozzle_state, percentage
    )


class BeverageEntityFeature(IntFlag):
    """Supported features of the beverage entity"""

    MAKE_BEVERAGE = 1
    SET_TEMPERATURE = 2
    SET_INTENCE = 4


class AvailableBeverage(StrEnum):
    """Coffee machine available beverages"""

    NONE = BEVERAGE_NONE
    STEAM = 'steam'
    LONG = 'long'
    COFFEE = 'coffee'
    DOPIO = 'dopio'
    HOTWATER = 'hot_water'
    ESPRESSO = 'espresso'
    AMERICANO = 'americano'
    ESPRESSO2 = 'espresso2'


class NotificationType(StrEnum):
    """Coffee machine notification types"""

    STATUS = 'status'
    PROCESS = 'process'


class BeverageCommand:
    """Coffee machine beverage commands"""

    def __init__(self, on, off):
        self.on = on
        self.off = off


class BeverageNotify:
    """Coffee machine beverage notifications"""

    def __init__(self, kind, description):
        self.kind = str(kind)
        self.description = str(description)


class DeviceSwitches:
    """All binary switches for the device"""

    def __init__(self):
        self.sounds = False
        self.energy_save = False
        self.cup_light = False
        self.filter = False
        self.is_on = False


BEVERAGE_COMMANDS = {
    AvailableBeverage.NONE: BeverageCommand(DEBUG, DEBUG),
    AvailableBeverage.STEAM: BeverageCommand(STEAM_ON, STEAM_OFF),
    AvailableBeverage.LONG: BeverageCommand(LONG_ON, LONG_OFF),
    AvailableBeverage.COFFEE: BeverageCommand(COFFE_ON, COFFE_OFF),
    AvailableBeverage.DOPIO: BeverageCommand(DOPPIO_ON, DOPPIO_OFF),
    AvailableBeverage.HOTWATER: BeverageCommand(HOTWATER_ON, HOTWATER_OFF),
    AvailableBeverage.ESPRESSO: BeverageCommand(ESPRESSO_ON, ESPRESSO_OFF),
    AvailableBeverage.AMERICANO: BeverageCommand(AMERICANO_ON, AMERICANO_OFF),
    AvailableBeverage.ESPRESSO2: BeverageCommand(ESPRESSO2_ON, ESPRESSO2_OFF),
}

# Map recipe IDs from MachinesModels.json to existing hardcoded commands
RECIPE_ID_TO_BEVERAGE = {
    1: AvailableBeverage.ESPRESSO,     # Espresso Coffee
    2: AvailableBeverage.COFFEE,       # Regular Coffee
    3: AvailableBeverage.LONG,         # Long Coffee
    4: AvailableBeverage.ESPRESSO2,    # 2X Espresso Coffee
    5: AvailableBeverage.DOPIO,        # Doppio+
    6: AvailableBeverage.AMERICANO,    # Americano
    16: AvailableBeverage.HOTWATER,    # Hot Water
    17: AvailableBeverage.STEAM,       # Steam
}


def _build_stop_command(recipe_id: int) -> list[int]:
    """Build a stop command for any recipe ID."""
    return [0x0D, 0x08, 0x83, 0xF0, recipe_id & 0xFF, 0x02, 0x06, 0x00, 0x00]


def _build_start_command(recipe_id: int, coffee_qty: int = 0,
                         milk_qty: int = 0) -> list[int]:
    """Build a generic start command for a recipe.

    The command structure varies by recipe type, but this covers the common
    coffee-only and milk-drink patterns observed from the DeLonghi protocol.
    """
    rid = recipe_id & 0xFF

    if milk_qty <= 0:
        # Coffee-only format
        return [
            0x0D, 0x0D, 0x83, 0xF0, rid, 0x01,
            0x01, 0x00, coffee_qty & 0xFF,
            0x00, 0x00, 0x06, 0x00, 0x00,
        ]

    # Milk drink format (observed for cappuccino-like beverages)
    milk_lo = milk_qty & 0xFF
    milk_hi = (milk_qty >> 8) & 0xFF
    return [
        0x0D, 0x0F, 0x83, 0xF0, rid, 0x01,
        0x01, 0x00, coffee_qty & 0xFF,
        0x02, 0x02, milk_hi, milk_lo,
        0x06, 0x00, 0x00,
    ]


DEVICE_NOTIFICATION = {
    str(bytearray(DEVICE_READY)): BeverageNotify(
        NotificationType.STATUS, 'DeviceOK'
    ),
    str(bytearray(DEVICE_TURNOFF)): BeverageNotify(
        NotificationType.STATUS, 'DeviceOFF'
    ),
    str(bytearray(WATER_TANK_DETACHED)): BeverageNotify(
        NotificationType.STATUS, 'NoWaterTank'
    ),
    str(bytearray(WATER_SHORTAGE)): BeverageNotify(
        NotificationType.STATUS, 'NoWater'
    ),
    str(bytearray(COFFEE_GROUNDS_CONTAINER_DETACHED)): BeverageNotify(
        NotificationType.STATUS, 'NoGroundsContainer'
    ),
    str(bytearray(COFFEE_GROUNDS_CONTAINER_FULL)): BeverageNotify(
        NotificationType.STATUS, 'GroundsContainerFull'
    ),
    str(bytearray(COFFEE_GROUNDS_CONTAINER_CLEAN)): BeverageNotify(
        NotificationType.STATUS, 'GroundsContainerFull'
    ),
    str(bytearray(START_COFFEE)): BeverageNotify(
        NotificationType.STATUS, 'START_COFFEE'
    ),
}


class DelongiPrimadonna:
    """Delongi Primadonna class"""

    def __init__(self, config: dict, hass: HomeAssistant) -> None:
        """Initialize device"""
        self._device_status = None
        self._client = None
        self._hass = hass
        self._device = None
        self._connecting = False
        self.mac = config.get(CONF_MAC)
        self.name = config.get(CONF_NAME)
        self.product_code = config.get(CONF_MODEL)
        self.hostname = ''
        self.friendly_name = ''
        self.cooking = BEVERAGE_NONE
        self.connected = False
        self.notify = False
        self.steam_nozzle = NOZZLE_STATE[-1]
        self.service = 0
        self.status = 'ready'
        self.switches = DeviceSwitches()
        self.active_switches: list[MachineSwitch] = []
        self.sync_time = False
        self.is_dispensing = False
        self.dispensing_percentage = 0
        self.last_time_sync = 0.0
        self._lock = asyncio.Lock()
        self._rx_buffer = bytearray()
        self._response_event = None
        self._expected_statistics_start: int | None = None
        self._last_response: bytes | None = None
        self.statistics: dict[int, int | float] = {}
        self._last_stats_request = 0.0
        self._stats_lock = asyncio.Lock()
        self._switches_raw: int | None = None
        self._last_switches_request = 0.0
        self._statistics_task: asyncio.Task | None = None
        self._initialization_task: asyncio.Task | None = None
        machine = get_machine_model(self.product_code)
        self.model = (
            machine.name if machine and machine.name else 'Prima Donna'
        )
        self.image_url = (
            machine.image_url if machine and machine.image_url
            else DEFAULT_IMAGE_URL
        )
        self._n_profiles = (
            machine.nProfiles
            if machine and machine.nProfiles
            else len(AVAILABLE_PROFILES)
        )
        # Per-device profile mapping so each instance keeps its own
        # names even when multiple machines are configured. The
        # module-level AVAILABLE_PROFILES is only used here as a
        # fallback source of default names; it is never mutated.
        self._profiles: dict[int, str] = {
            pid: AVAILABLE_PROFILES.get(pid, f"Profile {pid}")
            for pid in range(1, self._n_profiles + 1)
        }
        self.active_profile_id: int | None = None
        self.profiles = list(self._profiles.values())
        self._profiles_loaded = False

        # Build dynamic beverage list from machine recipes
        # name -> {id, coffee_qty, milk_qty}
        self._recipe_map: dict[str, dict] = {}
        self.available_beverages: list[str] = [BEVERAGE_NONE]
        if machine and machine.recipes:
            custom_idx = 0
            for recipe in machine.recipes:
                rname = recipe.name.value if recipe.name else None
                if rname and recipe.id is not None:
                    rid = int(recipe.id)
                    # Deduplicate: custom recipes get numbered names
                    if rname == "Custom":
                        custom_idx += 1
                        rname = f"Custom {custom_idx}"
                    elif rname in self._recipe_map:
                        rname = f"{rname} ({rid})"
                    self._recipe_map[rname] = {
                        'id': rid,
                        'coffee_qty': recipe.coffee_qty or 0,
                        'milk_qty': recipe.milk_qty or 0,
                    }
                    self.available_beverages.append(rname)
        if len(self.available_beverages) <= 1:
            # Fallback to legacy enum if no recipes
            self.available_beverages = [*AvailableBeverage]

    def set_initialization_task(self, task: asyncio.Task) -> None:
        """Track the device initialization task."""
        self._initialization_task = task

    async def cancel_initialization(self) -> None:
        """Cancel and wait for device initialization."""
        task = self._initialization_task
        self._initialization_task = None

        if task is None or task.done():
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    def schedule_statistics_update(self) -> None:
        """Schedule a statistics update when needed."""
        task = self._statistics_task
        if task is not None and not task.done():
            return

        if time.monotonic() - self._last_stats_request < 60:
            return

        self._statistics_task = self._hass.async_create_background_task(
            self._run_statistics_update(),
            "delonghi statistics update",
        )

    async def _run_statistics_update(self) -> None:
        """Run a managed statistics update."""
        try:
            await self.update_statistics()
        except asyncio.CancelledError:
            raise
        except Exception:
            _LOGGER.exception("Statistics update failed")

    async def cancel_statistics_update(self) -> None:
        """Cancel and wait for a pending statistics update."""
        task = self._statistics_task
        self._statistics_task = None

        if task is None or task.done():
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def disconnect(self):
        """Disconnect from the device."""
        _LOGGER.info("Disconnect from %s", self.mac)
        async with self._lock:
            client = self._client
            if client is not None and client.is_connected:
                try:
                    await asyncio.wait_for(client.disconnect(), timeout=5)
                except (
                    asyncio.TimeoutError,
                    Exception,
                ) as error:  # noqa: BLE001
                    _LOGGER.warning(
                        "Forced disconnect [%s]: %s",
                        type(error).__name__,
                        error
                    )
                finally:
                    self._client = None
                    self.connected = False
            else:
                self._client = None
                self.connected = False

    async def _connect(self):
        """Connect to the device."""
        if self._client is not None and self._client.is_connected:
            return

        self._client = None
        self.connected = False
        self._connecting = True
        try:
            self._device = bluetooth.async_ble_device_from_address(
                self._hass, self.mac, connectable=True
            )
            if not self._device:
                raise BleakError(
                    f"A device with address {self.mac} could not be found."
                )

            _LOGGER.info("Connect to %s", self.mac)
            client = await establish_connection(
                BleakClientWithServiceCache,
                self._device,
                self.name or self.mac,
                max_attempts=3,
            )
            self._client = client

            try:
                self._rx_buffer.clear()
                await asyncio.wait_for(
                    client.start_notify(
                        uuid.UUID(CONTROLL_CHARACTERISTIC),
                        self._process_raw_data,
                    ),
                    timeout=10,
                )
                self.connected = True
            except asyncio.CancelledError:
                try:
                    await asyncio.wait_for(client.disconnect(), timeout=5)
                except Exception:  # noqa: BLE001
                    pass
                finally:
                    self._client = None
                raise
            except Exception:
                try:
                    await asyncio.wait_for(client.disconnect(), timeout=5)
                except Exception:  # noqa: BLE001
                    pass
                finally:
                    self._client = None
                raise

        except Exception as error:
            self.connected = False
            _LOGGER.warning(
                "BLE connect error: %s (type: %s)",
                error,
                type(error).__name__,
            )
            raise
        finally:
            self._connecting = False

    def _make_switch_command(self):
        """Make hex command.

        Uses the last settings byte read from the device as base so
        that bits not managed by this integration (e.g. the cup warmer
        on some models) are preserved instead of being overwritten.
        """
        base = (
            self._switches_raw
            if self._switches_raw is not None
            else int(BASE_COMMAND, 2)
        )
        for bit, enabled in (
            (SWITCH_BIT_ENERGY_SAVE, self.switches.energy_save),
            (SWITCH_BIT_CUP_LIGHT, self.switches.cup_light),
            (SWITCH_BIT_SOUNDS, self.switches.sounds),
        ):
            base = base | bit if enabled else base & ~bit
        self._switches_raw = base
        hex_command = BYTES_SWITCH_COMMAND.copy()
        hex_command[9] = base
        return hex_command

    def _handle_parameter_data(self, value: bytes) -> None:
        """Handle a parameter read response (0x95).

        Layout: d0 <len> 95 0f <param_hi> <param_lo> <b3> <b2> <b1> <b0>
        <crc16>. Parameter 0x3f carries the settings bitmask; its low
        byte mirrors what BYTES_SWITCH_COMMAND writes.
        """
        if len(value) < 12:
            return
        param = (value[4] << 8) | value[5]
        if param != PARAM_SWITCHES:
            return
        raw = value[9]
        self._switches_raw = raw
        self.switches.cup_light = bool(raw & SWITCH_BIT_CUP_LIGHT)
        self.switches.sounds = bool(raw & SWITCH_BIT_SOUNDS)
        self.switches.energy_save = bool(raw & SWITCH_BIT_ENERGY_SAVE)
        _LOGGER.debug('Settings parameter 0x3f = 0x%02x', raw)

    async def update_switches(self) -> None:
        """Request the settings parameter with throttling."""
        current_time = time.monotonic()
        if current_time - self._last_switches_request < 30:
            return
        self._last_switches_request = current_time
        await self.send_command(BYTES_LOAD_SWITCHES.copy())

    async def _event_trigger(self, value):
        """
        Trigger event
        :param value: event value
        """
        event_data = {'data': str(hexlify(value, ' '))}

        notification_message = (
            str(hexlify(value, ' '))
            .replace(' ', ', 0x')
            .replace("b'", '[0x')
            .replace("'", ']')
        )

        if str(bytearray(value)) in DEVICE_NOTIFICATION:
            notification_message = DEVICE_NOTIFICATION.get(
                str(bytearray(value))
            ).description
            event_data.setdefault(
                'type', DEVICE_NOTIFICATION.get(str(bytearray(value))).kind
            )
            event_data.setdefault(
                'description',
                DEVICE_NOTIFICATION.get(str(bytearray(value))).description,
            )
        self._hass.bus.async_fire(f'{DOMAIN}_event', event_data)

        if self.notify:
            answer_id = f"{value[2]:02x}"
            await self._hass.services.async_call(
                'persistent_notification',
                'create',
                {
                    'message': notification_message,
                    'title': f'{self.name} {answer_id}',
                    'notification_id': f'{self.mac}_err_{uuid.uuid4()}',
                },
            )
        _LOGGER.info('Event triggered: %s', event_data)

    @staticmethod
    def _has_valid_crc(packet: bytes) -> bool:
        """Return whether an assembled BLE packet has a valid CRC."""
        if len(packet) < 4:
            return False

        expected_crc = int.from_bytes(packet[-2:], byteorder='big')
        actual_crc = crc_hqx(packet[:-2], 0x1D0F)
        return actual_crc == expected_crc

    async def _process_raw_data(self, sender, value):
        """Assemble incoming BLE packets and pass complete messages."""
        self._rx_buffer.extend(value)

        while True:
            if len(self._rx_buffer) < 2:
                return
            try:
                start_index = self._rx_buffer.index(START_BYTE)
            except ValueError:
                self._rx_buffer.clear()
                return

            if start_index > 0:
                del self._rx_buffer[:start_index]

            if len(self._rx_buffer) < 2:
                return

            msg_len = self._rx_buffer[1] + 1

            if len(self._rx_buffer) < msg_len:
                return

            packet = bytes(self._rx_buffer[:msg_len])

            if not self._has_valid_crc(packet):
                _LOGGER.debug(
                    "Discarding invalid BLE frame candidate: %s",
                    hexlify(packet, " "),
                )
                del self._rx_buffer[0]
                continue

            del self._rx_buffer[:msg_len]
            await self._handle_data(sender, packet)

    async def _handle_data(self, sender, value):
        """Handle notifications from the device."""
        answer_id = value[2] if len(value) > 2 else None
        expected_statistics_start = self._expected_statistics_start
        response_start = (
            ((value[4] << 8) | value[5])
            if answer_id == 0xA2 and len(value) >= 12
            else None
        )
        statistics_response_matches = (
            expected_statistics_start is not None
            and response_start is not None
            and response_start >= expected_statistics_start
        )

        if answer_id in [0x75, 0x70]:
            monitor_data = parse_monitor_data(value)
            if monitor_data:
                self._handle_monitor_data(monitor_data, answer_id, value)
        elif answer_id == 0xA4:
            parsed = {}
            try:
                parsed = self._parse_profile_response(
                    list(value)
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Failed to parse profile response: %s", err)
            if parsed:
                self._profiles.update(parsed)
            _LOGGER.debug(
                "Available profiles: %s",
                self._profiles
            )
            self.profiles = list(self._profiles.values())
        elif answer_id == 0xA9:
            profile_id = value[4] if len(value) > 4 else None
            status = value[5] if len(value) > 5 else None
            _LOGGER.debug(
                "Profile change response id=%s status=%s raw=%s",
                profile_id,
                status,
                hexlify(value, " "),
            )
            if profile_id is not None and status == 0:
                self.active_profile_id = profile_id
        elif answer_id == 0xA2:
            if statistics_response_matches:
                await self._parse_statistics(value)
            else:
                _LOGGER.debug(
                    "Ignoring unexpected statistics response: "
                    "expected start >= %s, got %s",
                    expected_statistics_start,
                    response_start,
                )
        elif answer_id == 0x95:
            self._handle_parameter_data(value)

        if (
            self._response_event is not None
            and not self._response_event.is_set()
        ):
            response_matches = (
                statistics_response_matches
                if expected_statistics_start is not None
                else answer_id != 0xA2
            )
            if response_matches:
                self._response_event.set()

        hex_value = hexlify(value, ' ')

        if self._device_status != hex_value:
            _LOGGER.info(
                'Received data: %s from %s',
                hex_value,
                sender
            )
            await self._event_trigger(value)

        self._device_status = hex_value

    def _handle_monitor_data(
        self, monitor_data: MonitorData, answer_id: int, raw_packet: bytes
    ) -> None:
        """Apply parsed monitor data to device state."""
        # Power state
        self.switches.is_on = monitor_data.status > 0

        # Dispensing: milk preparation (10) and hot water (11) are their
        # own states; 7 covers both idle and dispensing, and the progress
        # counter is what tells them apart - the same rule longshot uses
        # for EcamStatus::Busy.
        self.is_dispensing = (
            monitor_data.status in (10, 11)
            or (monitor_data.status == 7 and monitor_data.sub_status != 0)
        )
        self.dispensing_percentage = (
            monitor_data.percentage if self.is_dispensing else 0
        )

        # Nozzle state (only present in v2 / 0x75 packets)
        if monitor_data.nozzle_state != -1:
            self.steam_nozzle = NOZZLE_STATE.get(
                monitor_data.nozzle_state, NOZZLE_STATE[-1]
            )

        # Alarm bitmask — feeds the Descale binary sensor (bit 2)
        self.service = monitor_data.alarms

        # Display status: show first active alarm, or machine state
        if monitor_data.alarms > 0:
            for i in range(32):
                if (monitor_data.alarms >> i) & 1:
                    self.status = DEVICE_STATUS.get(i, 'unknown_alarm')
                    break
        else:
            self.status = MACHINE_STATUS.get(
                monitor_data.status,
                f"State {monitor_data.status}"
            )

        # Active switches (v2 only; v1 uses different byte offsets)
        if answer_id == 0x75:
            self.active_switches = parse_switches(raw_packet)

    def _parse_profile_response(
        self,
        data: list[int],
    ) -> dict[int, str]:
        """Parse profile names sent by the machine."""

        b = bytes(data)
        if len(b) < 4 or b[0] != 0xD0:
            raise ValueError("Wrong start byte")

        profiles: dict[int, str] = {}
        NAME_SIZE = 20
        NAME_OFFSET = 1
        NAME_HEADER = 4
        idx = NAME_HEADER
        for profile_index in range(1, self._n_profiles + 1):
            if idx + NAME_SIZE > len(b):
                break
            raw = b[idx:idx + NAME_SIZE]
            idx += NAME_SIZE + NAME_OFFSET
            # Names are UTF-16-BE and NUL-terminated inside their slot.
            # Cut at the terminator instead of decoding the padding, which
            # is what produced the UnicodeDecodeError on the whole reply.
            end = len(raw)
            for pos in range(0, len(raw) - 1, 2):
                if raw[pos] == 0 and raw[pos + 1] == 0:
                    end = pos
                    break
            name = raw[:end].decode("utf-16-be", errors="ignore").strip()
            if not name:
                # An empty slot says nothing about the ones after it.
                continue
            profiles.setdefault(profile_index, name)
        return profiles

    async def power_on(self) -> None:
        """Turn the device on."""
        await self.send_command(BYTES_POWER)

    async def power_off(self) -> None:
        """Put the device into standby."""
        await self.send_command(BYTES_POWER_OFF)

    async def cup_light_on(self) -> None:
        """Turn the cup light on."""
        self.switches.cup_light = True
        await self.send_command(self._make_switch_command())

    async def cup_light_off(self) -> None:
        """Turn the cup light off."""
        self.switches.cup_light = False
        await self.send_command(self._make_switch_command())

    async def energy_save_on(self):
        """Enable energy save mode"""
        self.switches.energy_save = True
        await self.send_command(self._make_switch_command())

    async def energy_save_off(self):
        """Enable energy save mode"""
        self.switches.energy_save = False
        await self.send_command(self._make_switch_command())

    async def sound_alarm_on(self):
        """Enable sound alarm"""
        self.switches.sounds = True
        await self.send_command(self._make_switch_command())

    async def sound_alarm_off(self):
        """Disable sound alarm"""
        self.switches.sounds = False
        await self.send_command(self._make_switch_command())

    async def beverage_start(self, beverage: str) -> None:
        """Start beverage by name (recipe or legacy enum)."""
        if beverage == BEVERAGE_NONE:
            return
        # Try recipe map (dynamic from machine model)
        recipe = self._recipe_map.get(beverage)
        if recipe:
            rid = recipe['id']
            # Use hardcoded command if available for this recipe ID
            legacy = RECIPE_ID_TO_BEVERAGE.get(rid)
            if legacy and legacy in BEVERAGE_COMMANDS:
                _LOGGER.info(
                    "Starting %s (recipe %d) via legacy",
                    beverage, rid,
                )
                await self.send_command(BEVERAGE_COMMANDS[legacy].on)
            else:
                _LOGGER.info(
                    "Starting %s (recipe %d) via dynamic",
                    beverage, rid,
                )
                cmd = _build_start_command(
                    rid, recipe['coffee_qty'], recipe['milk_qty']
                )
                await self.send_command(cmd)
            self.cooking = beverage
            return
        _LOGGER.warning("Unknown beverage: %s", beverage)

    async def beverage_cancel(self) -> None:
        """Cancel beverage"""
        if self.cooking == BEVERAGE_NONE:
            return
        recipe = self._recipe_map.get(self.cooking)
        if recipe:
            await self.send_command(_build_stop_command(recipe['id']))
        else:
            _LOGGER.warning("Cannot cancel unknown beverage: %s", self.cooking)
        self.cooking = BEVERAGE_NONE

    async def debug(self):
        """Send command which causes status reply"""
        await self.send_command(DEBUG)

    async def get_device_name(self):
        """
        Get device name
        :return: device name
        """
        async with self._lock:
            try:
                await self._connect()
                try:
                    self.hostname = bytes(
                        await self._client.read_gatt_char(
                            uuid.UUID(NAME_CHARACTERISTIC)
                        )
                    ).decode('utf-8')
                except BleakError as error:
                    _LOGGER.debug(
                        'Could not read NAME_CHARACTERISTIC: %s', error
                    )
                    self.hostname = self.name or DEFAULT_DEVICE_NAME
                await self._client.write_gatt_char(
                    uuid.UUID(CONTROLL_CHARACTERISTIC), bytearray(DEBUG)
                )
                self.connected = True
            except BleakDBusError as error:
                self.connected = False
                _LOGGER.warning('BleakDBusError: %s', error)
            except BleakError as error:
                self.connected = False
                _LOGGER.warning('BleakError: %s', error)
            except asyncio.exceptions.TimeoutError as error:
                self.connected = False
                _LOGGER.info('TimeoutError: %s at device connection', error)
            except asyncio.CancelledError:
                self.connected = False
                raise

        if self.connected and not self._profiles_loaded:
            command = BYTES_LOAD_PROFILES.copy()
            command[5] = self._n_profiles
            await self.send_command(command)
            # Default to first profile until the user switches
            if self.active_profile_id is None:
                self.active_profile_id = 1
            self._profiles_loaded = True

    async def set_time(self, dt: datetime) -> None:
        """Set device clock from provided datetime."""
        packet = BYTES_TIME_COMMAND.copy()
        packet[4] = dt.hour & 0xFF
        packet[5] = dt.minute & 0xFF
        await self.send_command(packet)

    def profile_name(self, profile_id: int | None) -> str | None:
        """Return the name for a profile id, or None if unknown."""
        if profile_id is None:
            return None
        return self._profiles.get(profile_id)

    def profile_id(self, name: str) -> int | None:
        """Return the id for a profile name, or None if unknown."""
        for pid, profile_name in self._profiles.items():
            if profile_name == name:
                return pid
        return None

    async def select_profile(self, profile_id) -> None:
        """select a profile."""
        _LOGGER.debug("Send select profile command id=%s", profile_id)
        message = [0x0D, 0x06, 0xA9, 0xF0, profile_id, 0xD7, 0xC0]
        await self.send_command(message)

    async def set_auto_power_off(self, power_off_interval) -> None:
        """Set auto power off time."""
        message = copy.deepcopy(BYTES_AUTOPOWEROFF_COMMAND)
        message[9] = power_off_interval
        await self.send_command(message)

    async def set_water_hardness(self, hardness_level) -> None:
        """Set water hardness"""
        message = copy.deepcopy(BYTES_WATER_HARDNESS_COMMAND)
        message[9] = hardness_level
        await self.send_command(message)

    async def set_water_temperature(self, temperature_level) -> None:
        """Set water temperature"""
        message = copy.deepcopy(BYTES_WATER_TEMPERATURE_COMMAND)
        message[9] = temperature_level
        await self.send_command(message)

    async def common_command(self, command: str) -> None:
        """Send custom BLE command"""
        message = [int(x, 16) for x in command.split(' ')]
        await self.send_command(message)

    async def send_command(self, message, retries=3) -> bool:
        """Send a command and report whether a reply arrived.

        Correlation is only exact for statistics (0xA2), which are matched
        on the requested start address. Every other command still uses the
        original "first frame after the write wins" rule, so an unrelated
        monitor frame can satisfy the wait. The return value is therefore
        only meaningful for 0xA2; ``get_statistics`` is its sole consumer.
        Do not treat True as an acknowledgement for other commands without
        adding per-answer-id correlation first (see PR #255).
        """
        async with self._lock:
            message_to_send = copy.deepcopy(message)
            for attempt in range(retries):
                try:
                    await self._connect()
                    crc = crc_hqx(bytearray(message_to_send[:-2]), 0x1D0F)
                    crc_bytes = crc.to_bytes(2, byteorder='big')
                    message_to_send[-2] = crc_bytes[0]
                    message_to_send[-1] = crc_bytes[1]
                    _LOGGER.info(
                        'Send command: %s',
                        hexlify(bytearray(message_to_send), " ")
                    )

                    self._response_event = asyncio.Event()
                    if (
                        len(message_to_send) > 5
                        and message_to_send[2] == 0xA2
                    ):
                        self._expected_statistics_start = (
                            message_to_send[4] << 8
                        ) | message_to_send[5]
                    else:
                        self._expected_statistics_start = None

                    response_received = False
                    try:
                        await self._client.write_gatt_char(
                            CONTROLL_CHARACTERISTIC,
                            bytearray(message_to_send),
                        )
                        try:
                            await asyncio.wait_for(
                                self._response_event.wait(),
                                timeout=10,
                            )
                            response_received = True
                        except asyncio.TimeoutError:
                            _LOGGER.warning(
                                'Timeout waiting for a reply to the %s '
                                'command: %s',
                                describe_command(message_to_send),
                                hexlify(bytearray(message_to_send), " ")
                            )
                    finally:
                        self._response_event = None
                        self._expected_statistics_start = None

                    return response_received
                except BleakError as error:
                    self.connected = False
                    _LOGGER.warning(
                        'BleakError: %s (attempt %d)',
                        error,
                        attempt + 1
                    )
                    if self._client is not None:
                        try:
                            await asyncio.wait_for(
                                self._client.disconnect(),
                                timeout=5,
                            )
                        except Exception:  # noqa: BLE001
                            pass
                    self._client = None
                    await asyncio.sleep(2)

            _LOGGER.error('Failed to send command after %d attempts', retries)
            return False

    async def _parse_statistics(self, data: bytes) -> None:
        """Parse statistics response"""
        if len(data) < 12:
            return

        hex_data = hexlify(data, " ").decode('utf-8')
        _LOGGER.debug("Statistics Parser. Raw: %s", hex_data)

        # The first parameter ID is implicit from bytes 4-5
        pid = (data[4] << 8) | data[5]
        val = int.from_bytes(data[6:10], byteorder='big')
        self.statistics[pid] = val
        _LOGGER.debug(
            "Statistics Parser.Parsed (Implicit): ID %s = %s", pid, val
        )

        # Subsequent parameters are in the format [ID 2B] + [Value 4B]
        current_offset = 10

        # Check if there is at least one more [ID 2B] + [Val 4B] block before
        # CRC (last 2 bytes)
        while current_offset + 6 <= len(data) - 2:
            pid = (data[current_offset] << 8) | data[current_offset + 1]
            val = int.from_bytes(
                data[current_offset + 2:current_offset + 6],
                byteorder='big'
            )
            self.statistics[pid] = val
            _LOGGER.debug(
                "Statistics Parser.Parsed (Explicit): ID %s = %s", pid, val
            )
            current_offset += 6

        # Calculate combined values for total coffee
        if 3000 in self.statistics or 3077 in self.statistics:
            total = self.statistics.get(3000, 0) + self.statistics.get(3077, 0)
            self.statistics[-3077] = total

        # Calculate combined values for total coffee with milk
        if 3001 in self.statistics or 3003 in self.statistics:
            total = self.statistics.get(3001, 0) + self.statistics.get(3003, 0)
            self.statistics[-3003] = total

        # Convert water quantity to liters (divide by 2000).
        # Use float division to preserve precision.
        if 106 in self.statistics:
            water_ml = self.statistics.get(106, 0)
            self.statistics[10106] = round(water_ml / 2000.0, 2)

    async def update_statistics(self) -> None:
        """Update statistics with throttling."""
        # Prevent concurrent updates from multiple sensors
        if self._stats_lock.locked():
            return

        async with self._stats_lock:
            current_time = time.monotonic()
            # Attempt statistics polling at most once every 60 seconds,
            # including failed attempts, to avoid repeated BLE retries.
            if current_time - self._last_stats_request < 60:
                return

            self._last_stats_request = current_time
            # Start sparse statistics sequence at parameter 100
            if not await self.get_statistics(100, 10):
                return
            await asyncio.sleep(0.3)

            # Extended maintenance counters. Kept at 110 as on master:
            # 110-119 covers 111, the milk cleaning counter that
            # sensor.py actually reads. The PR moved the start to 111
            # without explanation, which drops 110 and gains nothing.
            if not await self.get_statistics(110, 10):
                return
            await asyncio.sleep(0.3)

            # Coffee beverage totals (3000-3009)
            if not await self.get_statistics(3000, 10):
                return
            await asyncio.sleep(0.3)

            # Request cold milk, choco and tea statistics
            # Covers: 3017-3026 (3017=cold milk, 3021=choco, 3025=tea)
            if not await self.get_statistics(3017, 10):
                return
            await asyncio.sleep(0.3)

            # Request optional additional coffee totals range
            # Covers: 3077-3080 (3077 is combined with 3000 for total coffee)
            if not await self.get_statistics(3077, 4):
                return
            await asyncio.sleep(0.3)

    async def get_statistics(self, start_index: int, count: int) -> bool:
        """Get statistics from the machine"""
        message = copy.deepcopy(BYTES_STATISTICS_COMMAND)
        message[4] = (start_index >> 8) & 0xFF
        message[5] = start_index & 0xFF
        message[6] = count

        return await self.send_command(message)
