"""Delongi primadonna device description"""
import logging
from binascii import hexlify
from datetime import datetime

import pygatt
from homeassistant.backports.enum import StrEnum
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import ServiceRegistry
from homeassistant.helpers import device_registry as dr

from .const import (AMERICANO_OFF, AMERICANO_ON, BYTES_CUP_LIGHT_OFF,
                    BYTES_CUP_LIGHT_ON, BYTES_POWER, COFFE_OFF, COFFE_ON,
                    CONTROLL_CHARACTERISTIC, DEBUG, DOMAIN, DOPPIO_OFF,
                    DOPPIO_ON, ESPRESSO2_OFF, ESPRESSO2_ON, ESPRESSO_OFF,
                    ESPRESSO_ON, HOTWATER_OFF, HOTWATER_ON, LONG_OFF, LONG_ON,
                    NAME_CHARACTERISTIC, STEAM_OFF, STEAM_ON)

_LOGGER = logging.getLogger(__name__)


class AvailableBeverage(StrEnum):

    STEAM = 'steam'
    LONG = 'long'
    COFFEE = 'coffee'
    DOPIO = 'dopio'
    HOTWATER = 'hot_water'
    ESPRESSO = 'espresso'
    AMERICANO = 'americano'
    ESPRESSO2 = 'espresso2'
    NONE = 'none'


class BeverageCommand:

    def __init__(self, on, off):
        self.on = on
        self.off = off


BEVERAGE_COMMANDS = {
    AvailableBeverage.STEAM: BeverageCommand(STEAM_ON, STEAM_OFF),
    AvailableBeverage.LONG: BeverageCommand(LONG_ON, LONG_OFF),
    AvailableBeverage.COFFEE: BeverageCommand(COFFE_ON, COFFE_OFF),
    AvailableBeverage.DOPIO: BeverageCommand(DOPPIO_ON, DOPPIO_OFF),
    AvailableBeverage.HOTWATER: BeverageCommand(HOTWATER_ON, HOTWATER_OFF),
    AvailableBeverage.ESPRESSO: BeverageCommand(ESPRESSO_ON, ESPRESSO_OFF),
    AvailableBeverage.AMERICANO: BeverageCommand(AMERICANO_ON, AMERICANO_OFF),
    AvailableBeverage.ESPRESSO2: BeverageCommand(ESPRESSO2_ON, ESPRESSO2_OFF)
}


class DelonghiDeviceEntity:
    """Entity class for the Delonghi devices"""

    def __init__(self, delongh_device):
        """Init entity with the device"""
        self._attr_unique_id = \
            f'{delongh_device.mac}_{self.__class__.__name__}'
        self.device: DelongiPrimadonna = delongh_device

    @property
    def device_info(self):
        """Shared device info information"""
        return {
            'identifiers': {(DOMAIN, self.device.mac)},
            'connections': {
                (dr.CONNECTION_NETWORK_MAC, self.device.mac)
            },
            'name': self.device.name,
            'manufacturer': 'Delongi',
            'model': self.device.model
        }


def sign_request(bytes):
    """Request signer"""
    deviser = 0x1d0f
    for item in bytes[:len(bytes) - 2]:
        i3 = (((deviser << 8) | (deviser >> 8)) &
              0x0000ffff) ^ (item & 0xffff)
        i4 = i3 ^ ((i3 & 0xff) >> 4)
        i5 = i4 ^ ((i4 << 12) & 0x0000ffff)
        deviser = i5 ^ (((i5 & 0xff) << 5) & 0x0000ffff)
    signature = list((deviser & 0x0000ffff).to_bytes(2, byteorder='big'))
    bytes[len(bytes) - 2] = signature[0]
    bytes[len(bytes) - 1] = signature[1]
    return bytes


class DelongiPrimadonna:
    """Delongi Primadonna class"""

    def __init__(self, config: dict, services: ServiceRegistry) -> None:
        """Initialize."""
        self.mac = config.get(CONF_MAC)
        self.name = config.get(CONF_NAME)
        self.hostname = ''
        self.error_count = 0
        self.model = 'Prima Donna'
        self.friendly_name = ''
        self.services = services
        self.cooking = AvailableBeverage.NONE
        self._adapter = pygatt.GATTToolBackend()
        self._adapter.start(reset_on_start=False)
        self._device = None
        self._error_count = 0
        self._first_error = None

    def __del__(self):
        self._adapter.stop()

    async def _notify_on_error(self, error):
        """Add UI notification on error"""
        _LOGGER.error('Error %s %s', type(error), error)
        if self._error_count == 0:
            self._first_error = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
        self._error_count = self._error_count + 1
        await self.services.async_call(
            'persistent_notification',
            'create',
            {
                'message': 'First error at ' +
                self._first_error + ' total errors ' + self._error_count,
                'title': f'{self.name} {self.mac}',
                'notification_id': f'{self.mac}_err'
            }
        )

    async def _dismiss_notification(self):
        """Remove UI notification the error dismissed"""
        self._error_count = 0
        self._first_error = None
        await self.services.async_call(
            'persistent_notification',
            'dismiss',
            {'notification_id': f'{self.mac}_err'}
        )

    async def _connect(self):
        if self._device is None:
            try:
                self._device = self._adapter.connect(self.mac, timeout=20)
                self._device.subscribe(
                    CONTROLL_CHARACTERISTIC, callback=self._handle_data)
                self._dismiss_notification()
            except pygatt.exceptions.NotConnectedError:
                self._device = None
        return self._device

    def _handle_data(self, handle, value):
        _LOGGER.info('Received data: %s', hexlify(value, ' '))
        self.services.call(
            'persistent_notification',
            'create',
            {
                'message': hexlify(value, ' ').decode('utf-8'),
                'title': f'{self.name} {self.mac}',
                'notification_id': f'{self.mac}_debug'
            }
        )

    async def _not_connected_handler(self, error):
        self._device = None
        await self._notify_on_error(error)
        await self._connect()

    @property
    def connected(self):
        return self._device is not None

    async def power_on(self) -> None:
        """Turn the device on."""
        await self._connect()
        if self.connected:
            try:
                self._device.char_write(
                    CONTROLL_CHARACTERISTIC,
                    bytearray(BYTES_POWER))
            except pygatt.exceptions.NotConnectedError as error:
                await self._not_connected_handler(error)

    async def cup_light_on(self) -> None:
        """Turn the cup light on."""
        await self._connect()
        if self.connected:
            try:
                self._device.char_write(
                    CONTROLL_CHARACTERISTIC,
                    bytearray(BYTES_CUP_LIGHT_ON))
            except pygatt.exceptions.NotConnectedError as error:
                await self._not_connected_handler(error)

    async def cup_light_off(self) -> None:
        """Turn the cup light off."""
        await self._connect()
        if self.connected:
            try:
                self._device.char_write(
                    CONTROLL_CHARACTERISTIC,
                    bytearray(BYTES_CUP_LIGHT_OFF))
                _LOGGER.warning('written')
            except pygatt.exceptions.NotConnectedError as error:
                await self._not_connected_handler(error)

    async def beverage_start(self, beverage: AvailableBeverage) -> None:
        """Start beverage"""
        await self._connect()
        if self.connected:
            try:
                self._device.char_write(
                    CONTROLL_CHARACTERISTIC,
                    bytearray(BEVERAGE_COMMANDS.get(beverage).on))
            except pygatt.exceptions.NotConnectedError as error:
                await self._not_connected_handler(error)
            finally:
                self.cooking = AvailableBeverage.NONE

    async def beverage_cancel(self) -> None:
        """Cancel beverage"""
        await self._connect()
        if self.connected and self.cooking != AvailableBeverage.NONE:
            try:
                self._device.char_write(
                    CONTROLL_CHARACTERISTIC,
                    bytearray(BEVERAGE_COMMANDS.get(self.cooking).off))
            except pygatt.exceptions.NotConnectedError as error:
                await self._not_connected_handler(error)
            finally:
                self.cooking = AvailableBeverage.NONE

    async def debug(self):
        await self._connect()
        if self.connected:
            try:
                self._device.char_write(CONTROLL_CHARACTERISTIC,
                                        bytearray(DEBUG))
            except pygatt.exceptions.NotConnectedError as error:
                await self._not_connected_handler(error)

    async def get_device_name(self):
        await self._connect()
        if self.connected:
            try:
                data = self._device.char_read(
                    NAME_CHARACTERISTIC).decode('utf-8')
                self.hostname = data
            except pygatt.exceptions.NotificationTimeout:
                _LOGGER.warn('Notification timeout')
            except pygatt.exceptions.NotConnectedError as error:
                await self._not_connected_handler(error)
