"""High level helpers used by the Home Assistant entities.

This module exposes the :class:`DelongiPrimadonna` BLE client together with
entity base classes and a deprecated utility for manually generating CRC
signatures.  It provides an abstraction layer between Home Assistant and the
raw protocol messages defined in :mod:`ble_client` and :mod:`message_parser`.
"""

from __future__ import annotations

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
    "DelonghiDeviceEntity"
]


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
