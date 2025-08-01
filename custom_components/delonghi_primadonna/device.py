"""High level helpers used by the Home Assistant entities.

This module exposes the :class:`DelongiPrimadonna` BLE client together with
entity base classes and a deprecated utility for manually generating CRC
signatures.  It provides an abstraction layer between Home Assistant and the
raw protocol messages defined in :mod:`ble_client` and :mod:`message_parser`.
"""

from __future__ import annotations

import logging
import warnings
from binascii import hexlify

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .ble_client import DelongiPrimadonna
from .const import DOMAIN
from .models import (BEVERAGE_COMMANDS, DEVICE_NOTIFICATION, DEVICE_STATUS,
                     NOZZLE_STATE, SERVICE_STATE, AvailableBeverage,
                     BeverageCommand, BeverageEntityFeature, BeverageNotify,
                     DeviceSwitches, NotificationType)

__all__ = [
    "DelongiPrimadonna",
    "AvailableBeverage",
    "BeverageEntityFeature",
    "DeviceSwitches",
    "DEVICE_STATUS",
    "NOZZLE_STATE",
    "SERVICE_STATE",
    "BEVERAGE_COMMANDS",
    "NotificationType",
    "BeverageCommand",
    "BeverageNotify",
    "DEVICE_NOTIFICATION",
    "DelonghiDeviceEntity",
    "sign_request",
]

_LOGGER = logging.getLogger(__name__)


class DelonghiDeviceEntity:
    """Entity class for the Delonghi devices."""

    _attr_has_entity_name = True

    def __init__(
        self, delongh_device: DelongiPrimadonna, hass: HomeAssistant
    ) -> None:
        self._attr_unique_id = (
            f"{delongh_device.mac}_{self.__class__.__name__}"
        )
        self.device = delongh_device
        self.hass = hass

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delonghi",
            "model": self.device.model,
        }


def sign_request(message: list[int]) -> None:
    """Deprecated manual CRC signer."""
    warnings.warn(
        "sign_request is deprecated, use binascii.crc_hqx instead",
        DeprecationWarning,
        stacklevel=2,
    )
    _LOGGER.warning(
        "sign_request is deprecated and will be removed in a future release. "
        "Use binascii.crc_hqx instead.",
    )
    _LOGGER.debug("Signing request: %s", hexlify(bytearray(message), " "))
    deviser = 0x1D0F
    for item in message[: len(message) - 2]:
        i3 = (((deviser << 8) | (deviser >> 8)) & 0x0000FFFF) ^ (item & 0xFFFF)
        i4 = i3 ^ ((i3 & 0xFF) >> 4)
        i5 = i4 ^ ((i4 << 12) & 0x0000FFFF)
        deviser = i5 ^ (((i5 & 0xFF) << 5) & 0x0000FFFF)
    signature = list((deviser & 0x0000FFFF).to_bytes(2, byteorder="big"))
    message[len(message) - 2] = signature[0]
    message[len(message) - 1] = signature[1]
    _LOGGER.debug(
        "Request signature bytes: %s %s", hex(signature[0]), hex(signature[1])
    )
