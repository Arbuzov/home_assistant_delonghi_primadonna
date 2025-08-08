"""Bluetooth client used by the integration to talk to coffee machines.

This module wraps :class:`~bleak.BleakClient` and exposes high level helper
methods to send commands to the device and process replies.  It also
implements reconnection logic and publishes Home Assistant events when the
machine notifies about state changes.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import uuid
from binascii import crc_hqx, hexlify

from bleak import BleakClient
from bleak.exc import BleakDBusError, BleakError
from homeassistant.components import bluetooth
from homeassistant.const import CONF_MAC, CONF_MODEL, CONF_NAME
from homeassistant.core import HomeAssistant

from .const import (AVAILABLE_PROFILES, BASE_COMMAND,
                    BYTES_AUTOPOWEROFF_COMMAND, BYTES_LOAD_PROFILES,
                    BYTES_POWER, BYTES_SWITCH_COMMAND,
                    BYTES_WATER_HARDNESS_COMMAND,
                    BYTES_WATER_TEMPERATURE_COMMAND, CONTROLL_CHARACTERISTIC,
                    DEBUG, NAME_CHARACTERISTIC)
from .machine_switch import MachineSwitch
from .message_parser import MessageParser
from .model import get_machine_model
from .models import (BEVERAGE_COMMANDS, DEVICE_STATUS, NOZZLE_STATE,
                     AvailableBeverage, DeviceSwitches)
from .statistics import StatisticsReader

_LOGGER = logging.getLogger(__name__)


class DelongiPrimadonna(MessageParser):
    """Handle low-level BLE communication with the coffee machine.

    This class manages the connection lifecycle, sends prepared byte
    commands and feeds every received packet into :class:`MessageParser`
    for decoding.  Home Assistant entities keep a reference to an instance
    of this client to perform actions on the device.
    """

    def __init__(self, config: dict, hass: HomeAssistant) -> None:
        """Initialize device."""
        self._device_status = None
        self._client = None
        self._hass = hass
        self._device = None
        self._connecting = False
        self.mac = config.get(CONF_MAC)
        self.name = config.get(CONF_NAME)
        self.product_code = config.get(CONF_MODEL)
        self.hostname = ""
        self.model = "Prima Donna"
        self.friendly_name = ""
        self.cooking = AvailableBeverage.NONE
        self.connected = False
        self.notify = False
        self.steam_nozzle = NOZZLE_STATE[-1]
        self.service = 0
        self.status = DEVICE_STATUS[5]
        self.switches = DeviceSwitches()
        self.active_switches: list[MachineSwitch] = []
        self._lock = asyncio.Lock()
        self._rx_buffer = bytearray()
        self._response_event = None
        self._last_response: bytes | None = None
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

    async def disconnect(self) -> None:
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
                        error,
                    )
                finally:
                    self._client = None
                    self.connected = False
            else:
                self._client = None
                self.connected = False

    async def _connect(self, retries: int = 3) -> None:
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
                                f"A device with address {self.mac} "
                                "could not be found."
                            )
                        )
                    self._client = BleakClient(self._device)
                    _LOGGER.info(
                        "Connect to %s (attempt %d)", self.mac, attempt + 1
                    )
                    await asyncio.wait_for(self._client.connect(), timeout=10)
                    await asyncio.wait_for(
                        self._client.start_notify(
                            uuid.UUID(CONTROLL_CHARACTERISTIC),
                            self._process_raw_data,
                        ),
                        timeout=10,
                    )
                self._connecting = False
                return
            except Exception as error:  # noqa: BLE001
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

    def _make_switch_command(self) -> list[int]:
        base_command = list(BASE_COMMAND)
        base_command[3] = "1" if self.switches.energy_save else "0"
        base_command[4] = "1" if self.switches.cup_light else "0"
        base_command[5] = "1" if self.switches.sounds else "0"
        hex_command = BYTES_SWITCH_COMMAND.copy()
        hex_command[9] = int("".join(base_command), 2)
        return hex_command

    async def power_on(self) -> None:
        await self.send_command(BYTES_POWER)

    async def cup_light_on(self) -> None:
        self.switches.cup_light = True
        await self.send_command(self._make_switch_command())

    async def cup_light_off(self) -> None:
        self.switches.cup_light = False
        await self.send_command(self._make_switch_command())

    async def energy_save_on(self) -> None:
        self.switches.energy_save = True
        await self.send_command(self._make_switch_command())

    async def energy_save_off(self) -> None:
        self.switches.energy_save = False
        await self.send_command(self._make_switch_command())

    async def sound_alarm_on(self) -> None:
        self.switches.sounds = True
        await self.send_command(self._make_switch_command())

    async def sound_alarm_off(self) -> None:
        self.switches.sounds = False
        await self.send_command(self._make_switch_command())

    async def beverage_start(self, beverage: AvailableBeverage) -> None:
        await self.send_command(BEVERAGE_COMMANDS.get(beverage).on)

    async def beverage_cancel(self) -> None:
        if self.cooking != AvailableBeverage.NONE:
            await self.send_command(BEVERAGE_COMMANDS.get(self.cooking).off)

    async def debug(self) -> None:
        await self.send_command(DEBUG)

    async def get_device_name(self) -> None:
        async with self._lock:
            try:
                await self._connect()
                self.hostname = bytes(
                    await self._client.read_gatt_char(
                        uuid.UUID(NAME_CHARACTERISTIC)
                    )
                ).decode("utf-8")
                await self._client.write_gatt_char(
                    uuid.UUID(CONTROLL_CHARACTERISTIC), bytearray(DEBUG)
                )
                self.connected = True
            except BleakDBusError as error:
                self.connected = False
                _LOGGER.warning("BleakDBusError: %s", error)
            except BleakError as error:
                self.connected = False
                _LOGGER.warning("BleakError: %s", error)
            except asyncio.TimeoutError as error:
                self.connected = False
                _LOGGER.info("TimeoutError: %s at device connection", error)
            except asyncio.CancelledError as error:
                self.connected = False
                _LOGGER.warning("CancelledError: %s", error)
        if self.connected and not self._profiles_loaded:
            command = BYTES_LOAD_PROFILES.copy()
            command[5] = self._n_profiles
            await self.send_command(command)
            self._profiles_loaded = True

    async def select_profile(self, profile_id: int) -> None:
        _LOGGER.debug("Send select profile command id=%s", profile_id)
        message = [0x0D, 0x06, 0xA9, 0xF0, profile_id, 0xD7, 0xC0]
        await self.send_command(message)

    async def set_auto_power_off(self, power_off_interval: int) -> None:
        message = copy.deepcopy(BYTES_AUTOPOWEROFF_COMMAND)
        message[9] = power_off_interval
        await self.send_command(message)

    async def set_water_hardness(self, hardness_level: int) -> None:
        message = copy.deepcopy(BYTES_WATER_HARDNESS_COMMAND)
        message[9] = hardness_level
        await self.send_command(message)

    async def set_water_temperature(self, temperature_level: int) -> None:
        message = copy.deepcopy(BYTES_WATER_TEMPERATURE_COMMAND)
        message[9] = temperature_level
        await self.send_command(message)

    async def common_command(self, command: str) -> None:
        message = [int(x, 16) for x in command.split(" ")]
        await self.send_command(message)

    async def read_statistics(self) -> None:
        """Request statistical parameters from the coffee machine.

        This coroutine no longer returns parsed statistics; callers should
        consume logged output instead.
        """
        await StatisticsReader(self).request_all()

    async def send_command(self, message, retries: int = 3) -> bytes | None:
        async with self._lock:
            message_to_send = copy.deepcopy(message)
            for attempt in range(retries):
                try:
                    await self._connect()
                    crc = crc_hqx(bytearray(message_to_send[:-2]), 0x1D0F)
                    crc_bytes = crc.to_bytes(2, byteorder="big")
                    message_to_send[-2] = crc_bytes[0]
                    message_to_send[-1] = crc_bytes[1]
                    _LOGGER.info(
                        "Send command: %s",
                        hexlify(bytearray(message_to_send), " "),
                    )
                    self._response_event = asyncio.Event()
                    self._last_response = None
                    await self._client.write_gatt_char(
                        CONTROLL_CHARACTERISTIC, bytearray(message_to_send)
                    )
                    try:
                        await asyncio.wait_for(
                            self._response_event.wait(), timeout=10
                        )
                    except asyncio.TimeoutError:
                        _LOGGER.warning(
                            "Timeout waiting for response to command: %s",
                            hexlify(bytearray(message_to_send), " "),
                        )
                    finally:
                        self._response_event = None
                    return self._last_response
                except BleakError as error:
                    self.connected = False
                    self._client = None
                    _LOGGER.warning(
                        "BleakError: %s (attempt %d)", error, attempt + 1
                    )
                    await asyncio.sleep(2)
            _LOGGER.error("Failed to send command after %d attempts", retries)
            return None
