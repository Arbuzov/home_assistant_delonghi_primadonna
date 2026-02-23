"""Delongi primadonna device description"""
import asyncio
import copy

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - fallback for older Home Assistant
    from homeassistant.backports.enum import StrEnum

import logging
import uuid
from binascii import crc_hqx, hexlify
from datetime import datetime
from enum import IntFlag

from bleak import BleakClient
from bleak.exc import BleakDBusError, BleakError
from homeassistant.components import bluetooth
from homeassistant.const import CONF_MAC, CONF_MODEL, CONF_NAME
from homeassistant.core import HomeAssistant
import time
from dataclasses import dataclass

from .const import (AMERICANO_OFF, AMERICANO_ON, AVAILABLE_PROFILES,
                    BASE_COMMAND, BYTES_AUTOPOWEROFF_COMMAND,
                    BYTES_LOAD_PROFILES, BYTES_POWER, BYTES_SWITCH_COMMAND,
                    BYTES_TIME_COMMAND, BYTES_WATER_HARDNESS_COMMAND,
                    BYTES_WATER_TEMPERATURE_COMMAND, BYTES_STATISTICS_COMMAND,
                    COFFE_OFF, COFFE_ON,
                    COFFEE_GROUNDS_CONTAINER_CLEAN,
                    COFFEE_GROUNDS_CONTAINER_DETACHED,
                    COFFEE_GROUNDS_CONTAINER_FULL, CONTROLL_CHARACTERISTIC,
                    DEBUG, DEVICE_READY, DEVICE_STATUS, DEVICE_TURNOFF, DOMAIN,
                    DOPPIO_OFF, DOPPIO_ON, ESPRESSO2_OFF, ESPRESSO2_ON,
                    ESPRESSO_OFF, ESPRESSO_ON, HOTWATER_OFF, HOTWATER_ON,
                    LONG_OFF, LONG_ON, NAME_CHARACTERISTIC, NOZZLE_STATE,
                    START_COFFEE, STEAM_OFF, STEAM_ON, WATER_SHORTAGE,
                    WATER_TANK_DETACHED)
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

    if answer_id == 0x75: # MonitorDataV2
        if len(data) < 14:
            return None
        # Switches: Bytes 5, 6 (Little Endian)
        switches = data[5] + (data[6] << 8)
        
        # Alarms: Bytes 7, 8, 12, 13 (Little Endian in blocks)
        # Based on MonitorDataV2.b():
        # iS = z.S(bArr[7]) + (z.S(bArr[8]) << 8) + (z.S(bArr[12]) << 16) + (z.S(bArr[13]) << 24)
        alarms = data[7] + (data[8] << 8) + (data[12] << 16) + (data[13] << 24)
        
        # Status/State: Byte 9
        status = data[9]
        
        # SubStatus: Byte 10
        sub_status = data[10]
        
        # Nozzle State: Byte 4 (from MonitorDataV2.a())
        nozzle_state = data[4]
        
    elif answer_id == 0x70: # MonitorData (v1)
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
        
    return MonitorData(switches, alarms, status, sub_status, nozzle_state)



class BeverageEntityFeature(IntFlag):
    """Supported features of the beverage entity"""

    MAKE_BEVERAGE = 1
    SET_TEMPERATURE = 2
    SET_INTENCE = 4


class AvailableBeverage(StrEnum):
    """Coffee machine available beverages"""

    NONE = 'none'
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
        self.model = 'Prima Donna'
        self.friendly_name = ''
        self.cooking = AvailableBeverage.NONE
        self.connected = False
        self.notify = False
        self.steam_nozzle = NOZZLE_STATE[-1]
        self.service = 0
        self.status = DEVICE_STATUS[5]
        self.switches = DeviceSwitches()
        self.active_switches: list[MachineSwitch] = []
        self.sync_time = False
        self._lock = asyncio.Lock()
        self._rx_buffer = bytearray()
        self._response_event = None
        self._last_response: bytes | None = None
        self.statistics: dict[int, int | float] = {}
        self._last_stats_request = 0.0
        self._stats_lock = asyncio.Lock()
        machine = get_machine_model(self.product_code)
        self._n_profiles = (
            machine.nProfiles
            if machine and machine.nProfiles
            else len(AVAILABLE_PROFILES)
        )
        for pid in range(1, self._n_profiles + 1):
            AVAILABLE_PROFILES.setdefault(pid, f"Profile {pid}")
        for pid in list(AVAILABLE_PROFILES):
            if pid > self._n_profiles:
                AVAILABLE_PROFILES.pop(pid)
        self.profiles = list(AVAILABLE_PROFILES.values())
        self._profiles_loaded = False

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

    async def _connect(self, retries=3):
        """Connect to the device."""
        self._connecting = True
        last_error = None
        for attempt in range(retries):
            try:
                if self._client is None or not self._client.is_connected:
                    self._device = bluetooth.async_ble_device_from_address(
                        self._hass, self.mac, connectable=True
                    )
                    if not self._device:
                        raise BleakError(
                            (
                                f"A device with address {self.mac}"
                                " could not be found."
                            )
                        )
                    self._client = BleakClient(self._device)
                    _LOGGER.info(
                        "Connect to %s (attempt %d)",
                        self.mac,
                        attempt + 1,
                    )
                    await asyncio.wait_for(
                        self._client.connect(),
                        timeout=10,
                    )
                    # Service discovery is performed during the connection
                    # process. Accessing ``get_services`` directly raises a
                    # ``FutureWarning`` in recent versions of Bleak.
                    # ``self._client.services`` will contain the discovered
                    # services once the connection succeeds.
                    await asyncio.wait_for(
                        self._client.start_notify(
                            uuid.UUID(CONTROLL_CHARACTERISTIC),
                            self._process_raw_data,
                        ),
                        timeout=10,
                    )
                self._connecting = False
                return
            except Exception as error:
                _LOGGER.warning(
                    "BLE connect error: %s (type: %s, attempt %d)",
                    error,
                    type(error).__name__,
                    attempt + 1,
                )
                if self._client is not None:
                    try:
                        await asyncio.wait_for(
                            self._client.disconnect(), timeout=5
                        )
                    except Exception:  # noqa: BLE001
                        pass
                self._client = None
                last_error = error
                await asyncio.sleep(2)
        self._connecting = False
        raise last_error

    def _make_switch_command(self):
        """Make hex command"""
        base_command = list(BASE_COMMAND)
        base_command[3] = '1' if self.switches.energy_save else '0'
        base_command[4] = '1' if self.switches.cup_light else '0'
        base_command[5] = '1' if self.switches.sounds else '0'
        hex_command = BYTES_SWITCH_COMMAND.copy()
        hex_command[9] = int(''.join(base_command), 2)
        return hex_command

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
            del self._rx_buffer[:msg_len]
            await self._handle_data(sender, packet)

    async def _handle_data(self, sender, value):
        """Handle notifications from the device."""
        if (
            self._response_event is not None
            and not self._response_event.is_set()
        ):
            self._response_event.set()
        answer_id = value[2] if len(value) > 2 else None

        if answer_id in [0x75, 0x70]:
            monitor_data = parse_monitor_data(value)
            if monitor_data:
                self._handle_monitor_data(monitor_data, answer_id, value)
        elif answer_id == 0xA4:
            parsed = []
            try:
                parsed = self._parse_profile_response(
                    list(value)
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Failed to parse profile response: %s", err)
            for pid, name in parsed.items():
                AVAILABLE_PROFILES[pid] = name
            _LOGGER.debug(
                "Available profiles: %s",
                AVAILABLE_PROFILES
            )
            self.profiles = list(AVAILABLE_PROFILES.values())
        elif answer_id == 0xA9:
            profile_id = value[4] if len(value) > 4 else None
            status = value[5] if len(value) > 5 else None
            _LOGGER.debug(
                "Profile change response id=%s status=%s raw=%s",
                profile_id,
                status,
                hexlify(value, " "),
            )
        elif answer_id == 0xA2:
            await self._parse_statistics(value)

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

        # Nozzle state (only present in v2 / 0x75 packets)
        if monitor_data.nozzle_state != -1:
            self.steam_nozzle = NOZZLE_STATE.get(
                monitor_data.nozzle_state, monitor_data.nozzle_state
            )

        # Alarm bitmask — feeds the Descale binary sensor (bit 2)
        self.service = monitor_data.alarms

        # Display status: show first active alarm, or machine state
        if monitor_data.alarms > 0:
            for i in range(32):
                if (monitor_data.alarms >> i) & 1:
                    self.status = DEVICE_STATUS.get(i, f"Alarm {i}")
                    break
        elif monitor_data.status in (0, 1, 5):
            self.status = "Ready"
        else:
            self.status = f"State {monitor_data.status}"

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
        profile_index = 1
        idx = NAME_HEADER
        while idx + NAME_SIZE < len(b):
            profiles.setdefault(
                profile_index,
                b[idx:idx + NAME_SIZE]
                .decode("utf-16-be")
                .rstrip("\x00")
                .strip(),
            )
            profile_index += 1
            idx += NAME_SIZE + NAME_OFFSET
        return profiles

    async def power_on(self) -> None:
        """Turn the device on."""
        await self.send_command(BYTES_POWER)

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

    async def beverage_start(self, beverage: AvailableBeverage) -> None:
        """Start beverage"""
        await self.send_command(BEVERAGE_COMMANDS.get(beverage).on)

    async def beverage_cancel(self) -> None:
        """Cancel beverage"""
        if self.cooking != AvailableBeverage.NONE:
            await self.send_command(BEVERAGE_COMMANDS.get(self.cooking).off)

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
                self.hostname = bytes(
                    await self._client.read_gatt_char(
                        uuid.UUID(NAME_CHARACTERISTIC)
                    )
                ).decode('utf-8')
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
            except asyncio.exceptions.CancelledError as error:
                self.connected = False
                _LOGGER.warning('CancelledError: %s', error)

        if self.connected and not self._profiles_loaded:
            command = BYTES_LOAD_PROFILES.copy()
            command[5] = self._n_profiles
            await self.send_command(command)
            self._profiles_loaded = True

    async def set_time(self, dt: datetime) -> None:
        """Set device clock from provided datetime."""
        packet = BYTES_TIME_COMMAND.copy()
        packet[4] = dt.hour & 0xFF
        packet[5] = dt.minute & 0xFF
        await self.send_command(packet)

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

    async def send_command(self, message, retries=3):
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
                    await self._client.write_gatt_char(
                        CONTROLL_CHARACTERISTIC, bytearray(message_to_send)
                    )
                    try:
                        await asyncio.wait_for(
                            self._response_event.wait(),
                            timeout=10,
                        )
                    except asyncio.TimeoutError:
                        _LOGGER.warning(
                            'Timeout waiting for response to command: %s',
                            hexlify(bytearray(message_to_send), " ")
                        )
                    finally:
                        self._response_event = None
                    return
                except BleakError as error:
                    self.connected = False
                    self._client = None
                    _LOGGER.warning(
                        'BleakError: %s (attempt %d)',
                        error,
                        attempt + 1
                    )
                    await asyncio.sleep(2)
            _LOGGER.error('Failed to send command after %d attempts', retries)

    async def _parse_statistics(self, data: bytes) -> None:
        """Parse statistics response"""
        if len(data) < 8:
            return
            
        hex_data = hexlify(data, " ").decode('utf-8')
        _LOGGER.debug("Statistics Parser. Raw: %s", hex_data)
        
        # [0]=D0 [1]=Len [2]=A2 [3]=0F [4-5]=StartAddr
        start_param_id = (data[4] << 8) | data[5]
        
        # Offset to first value (byte 6)
        current_offset = 6
        current_param_id = start_param_id
        
        # 1. First value belongs to StartAddr
        if current_offset + 4 <= len(data) - 2:
            val = int.from_bytes(data[current_offset:current_offset+4], byteorder='big')
            self.statistics[current_param_id] = val
            _LOGGER.debug("Statistics Parser.Parsed (Implicit): ID %s = %s", current_param_id, val)
            current_offset += 4
            
        # 2. Subsequent parameters are [ID 2B] + [Value 4B]
        while current_offset + 6 <= len(data) - 2:
            pid = (data[current_offset] << 8) | data[current_offset+1]
            val = int.from_bytes(data[current_offset+2:current_offset+6], byteorder='big')
            self.statistics[pid] = val
            _LOGGER.debug("Statistics Parser.Parsed (Explicit): ID %s = %s", pid, val)
            current_offset += 6
        
        # Calculate combined values for total coffee
        if 3000 in self.statistics:
            total = self.statistics[3000] + self.statistics.get(3077, 0)
            self.statistics[-3077] = total
            
        # Convert water quantity to liters (divide by 2000)
        # Use float division to preserve precision and round to 2 decimal places.
        if 106 in self.statistics:
            water_ml = self.statistics.get(106, 0)
            if water_ml > 0:
                self.statistics[10106] = round(water_ml / 2000.0, 2)

    async def update_statistics(self) -> None:
        """Update statistics with throttling.
        
        Requests statistics from the ECAM machine via BLE.
        Based on APK's parameter address mappings:
        - 100-109: Maintenance counters (water, descaling, filters)
        - 110-119: Extended maintenance counters (milk cleaning)
        - 3000-3009: Coffee beverage totals
        - 3077-3080: Additional coffee totals (combined with 3000 for total)
        """
        
        # Use a lock to prevent concurrent statistics updates from multiple sensors
        if self._stats_lock.locked():
            return

        async with self._stats_lock:
            current_time = time.monotonic()
            # Update at most once every 60 seconds
            if current_time - self._last_stats_request < 60:
                return

            self._last_stats_request = current_time
            # Request parameter range for maintenance counters
            # Covers: 100-109 (includes 106=water, 105=descale, 108=filter, etc.)
            await self.get_statistics(100, 10)
            await asyncio.sleep(0.3)
            
            # Request extended maintenance counters
            # Covers: 110-119 (includes 115=milk cleaning)
            await self.get_statistics(110, 10)
            await asyncio.sleep(0.3)
            
            # Request coffee statistics range
            # Covers: 3000-3009 (includes 3000=total black coffee, 3001=with milk, etc.)
            await self.get_statistics(3000, 10)
            await asyncio.sleep(0.3)
            
            # Request additional coffee totals range
            # Covers: 3077-3080 (3077 is combined with 3000 for total coffee)
            await self.get_statistics(3077, 4)
            await asyncio.sleep(0.3)
            
            # Optional: Request tea/other beverages if needed
            # await self.get_statistics(3025, 1)  # Tea counter

    async def get_statistics(self, start_index: int, count: int) -> None:
        """Get statistics from the machine"""
        message = copy.deepcopy(BYTES_STATISTICS_COMMAND)
        message[4] = (start_index >> 8) & 0xFF
        message[5] = start_index & 0xFF
        message[6] = count
        await self.send_command(message)