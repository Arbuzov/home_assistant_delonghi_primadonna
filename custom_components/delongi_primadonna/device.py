"""Delongi primadonna device description"""
from homeassistant.backports.enum import StrEnum
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import ServiceRegistry
import pygatt

from .const import CHARACTERISTIC, BYTES_POWER, BYTES_CUP_LIGHT_ON, BYTES_CUP_LIGHT_OFF


class AvailableBeverage(StrEnum):

    STEAM = 'steam'


class DelongiPrimadonna:
    """Delongi primadonna class"""

    def __init__(self, config: dict, services: ServiceRegistry) -> None:
        """Initialize."""
        self.mac = config.get(CONF_MAC)
        self.name = config.get(CONF_NAME)
        self.model = 'Prima Donna'
        self.adapter = pygatt.GATTToolBackend()
        self.services = services

    async def _notify_on_error(self, error):
        """Add UI notification on error"""
        await self.services.async_call(
            'persistent_notification',
            'create',
            {
                'message': error,
                'title': f"{self.name} {self.mac}",
                'notification_id': self.mac
            }
        )

    async def power_on(self) -> None:
        """Turn the device on."""
        try:
            self.adapter.start(reset_on_start=False)
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray(BYTES_POWER))
        except pygatt.exceptions.NotConnectedError as error:
            await self._notify_on_error(error)
        finally:
            self.adapter.stop()

    async def cup_light_on(self) -> None:
        """Turn the cup light on."""
        try:
            self.adapter.start(reset_on_start=False)
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray(BYTES_CUP_LIGHT_ON))
        except pygatt.exceptions.NotConnectedError as error:
            await self._notify_on_error(error)
        finally:
            self.adapter.stop()

    async def cup_light_off(self) -> None:
        """Turn the cup light off."""
        try:
            self.adapter.start(reset_on_start=False)
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray(BYTES_CUP_LIGHT_OFF))
        except pygatt.exceptions.NotConnectedError as error:
            await self._notify_on_error(error)
        finally:
            self.adapter.stop()

    async def coffe_long_start(self) -> None:
        """Prepare coffe long"""
        try:
            self.adapter.start(reset_on_start=False)
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray([
                    0x0d, 0x0f, 0x83, 0xf0, 0x03, 0x01, 0x01, 0x00,
                    0xa0, 0x02, 0x03, 0x00, 0x00, 0x06, 0x18, 0x7f
                ]))
        except pygatt.exceptions.NotConnectedError as error:
            await self._notify_on_error(error)
        finally:
            self.adapter.stop()

    async def coffe_long_cancel(self) -> None:
        """Cancel preparation"""
        try:
            self.adapter.start(reset_on_start=False)
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray([
                    0x0d, 0x08, 0x83, 0xf0, 0x03, 0x02, 0x06, 0xf3, 0x81
                ]))
        except pygatt.exceptions.NotConnectedError as error:
            await self._notify_on_error(error)
        finally:
            self.adapter.stop()
