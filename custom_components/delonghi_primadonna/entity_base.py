"""Entity base class and exports for Home Assistant integration.

This module provides the base entity class and re-exports important classes
for backward compatibility during migration from the old architecture.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .delonghi_ha_client import DelonghiPrimaDonnaHAClient
from .models import (BEVERAGE_COMMANDS, DEVICE_NOTIFICATION, DEVICE_STATUS,
                     NOZZLE_STATE, SERVICE_STATE, AvailableBeverage,
                     BeverageCommand, BeverageEntityFeature, BeverageNotify,
                     DeviceSwitches, NotificationType)

__all__ = [
    "DelonghiPrimaDonnaHAClient",
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
    """Base entity class for Delonghi devices.
    
    This provides common functionality for all Delonghi device entities,
    including device info and unique ID generation.
    """

    _attr_has_entity_name = True

    def __init__(
        self, delongh_device: DelonghiPrimaDonnaHAClient, hass: HomeAssistant
    ) -> None:
        """Initialize the entity."""
        self._attr_unique_id = (
            f"{delongh_device.mac}_{self.__class__.__name__}"
        )
        self.device = delongh_device
        self.hass = hass

    @property
    def device_info(self) -> dict:
        """Return device information for Home Assistant device registry."""
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delonghi",
            "model": "Prima Donna",
        }
