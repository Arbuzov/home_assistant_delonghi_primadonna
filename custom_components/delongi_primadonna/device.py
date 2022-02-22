"""Delongi primadonna device description"""
import pygatt
from homeassistant.backports.enum import StrEnum
from homeassistant.const import CONF_MAC, CONF_NAME

from .const import CHARACTERISTIC


class AvailableBeverage(StrEnum):

    STEAM = 'steam'


class DelongiPrimadonna:
    """Delongi primadonna class"""

    def __init__(self, config: dict) -> None:
        """Initialize."""
        self.mac = config.get(CONF_MAC)
        self.name = config.get(CONF_NAME)
        self.model = 'Prima Donna'
        self.adapter = pygatt.GATTToolBackend()

    def power_on(self) -> None:
        """Turn the device on."""
        try:
            self.adapter.start()
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray([0x0d, 0x07, 0x84, 0x0f, 0x02, 0x01, 0x55, 0x12]))

        finally:
            self.adapter.stop()

    def power_off(self) -> None:
        """Turn the device off."""
        try:
            self.adapter.start()
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray([0x0d, 0x07, 0x84, 0x0f, 0x02, 0x01, 0x55, 0x12]))

        finally:
            self.adapter.stop()

    def cup_light_on(self) -> None:
        """Turn the cup light on."""
        try:
            self.adapter.start()
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray([
                    0x0d, 0x0b, 0x90, 0x0f, 0x00, 0x3f,
                    0x00, 0x00, 0x00, 0x99, 0x39, 0x22
                ]))

        finally:
            self.adapter.stop()

    def cup_light_off(self) -> None:
        """Turn the cup light off."""
        try:
            self.adapter.start()
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray([
                    0x0d, 0x0b, 0x90, 0x0f, 0x00, 0x3f,
                    0x00, 0x00, 0x00, 0x91, 0xb8, 0x2a
                ]))

        finally:
            self.adapter.stop()

    def coffe_long_start(self) -> None:
        """Prepare coffe long"""
        try:
            self.adapter.start()
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray([
                    0x0d, 0x0f, 0x83, 0xf0, 0x03, 0x01, 0x01, 0x00,
                    0xa0, 0x02, 0x03, 0x00, 0x00, 0x06, 0x18, 0x7f
                ]))

        finally:
            self.adapter.stop()

    def coffe_long_cancel(self) -> None:
        """Cancel preparation"""
        try:
            self.adapter.start()
            device = self.adapter.connect(self.mac, timeout=20)
            device.char_write(
                CHARACTERISTIC,
                bytearray([
                    0x0d, 0x08, 0x83, 0xf0, 0x03, 0x02, 0x06, 0xf3, 0x81
                ]))

        finally:
            self.adapter.stop()
