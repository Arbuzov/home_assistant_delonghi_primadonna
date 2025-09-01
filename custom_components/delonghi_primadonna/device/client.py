"""Refactored Delonghi PrimaDonna client with proper separation of concerns.

This is the main entry point that assembles all the components together.
Each component has a single responsibility and clear interfaces.
"""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.const import CONF_MAC, CONF_MODEL, CONF_NAME
from homeassistant.core import HomeAssistant

from .ble_connection import BleConnection
from ..const import CONTROLL_CHARACTERISTIC
from .delonghi_device import DelonghiDevice
from .message_parser import DeviceStatus

_LOGGER = logging.getLogger(__name__)


class DelonghiPrimaDonnaClient:
    """Main client for Delonghi PrimaDonna coffee machines.
    
    This class assembles the device-layer components:
    - BleConnection: handles BLE transport
    - MessageProtocol: handles protocol specifics  
    - PureMessageParser: parses messages
    - DelonghiDevice: business logic
    
    This is a pure device client without HA-specific integrations.
    """

    def __init__(self, config: dict, hass: HomeAssistant) -> None:
        """Initialize the client."""
        self.mac = config.get(CONF_MAC)
        self.name = config.get(CONF_NAME, "PrimaDonna")
        self.product_code = config.get(CONF_MODEL)
        
        # Create the component stack
        self._connection = BleConnection(
            mac_address=self.mac,
            hass=hass,
            control_characteristic=CONTROLL_CHARACTERISTIC,
            notify_characteristic=CONTROLL_CHARACTERISTIC,  # Same for this device
        )
        
        self._device = DelonghiDevice(
            mac_address=self.mac,
            control_characteristic=CONTROLL_CHARACTERISTIC,
            notify_characteristic=CONTROLL_CHARACTERISTIC,
            connection=self._connection,
        )

    async def connect(self) -> None:
        """Connect to the device."""
        await self._device.connect()

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        await self._device.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._device.is_connected

    @property
    def current_status(self) -> DeviceStatus | None:
        """Get current device status."""
        return self._device.current_status

    @property
    def profiles(self) -> dict[int, str]:
        """Get available profiles."""
        return self._device.profiles

    @property
    def statistics(self) -> list[int]:
        """Get current statistics."""
        return self._device.statistics

    # Device operations - just delegate to the device layer
    async def power_on(self) -> None:
        """Turn on the device."""
        await self._device.power_on()

    async def set_profile(self, profile_id: int) -> None:
        """Set active profile."""
        await self._device.set_profile(profile_id)

    async def set_time(self, dt: datetime) -> None:
        """Set device clock."""
        await self._device.set_time(dt)

    async def request_statistics(self) -> None:
        """Request device statistics."""
        await self._device.request_statistics()

    # For backward compatibility during migration
    async def get_device_name(self) -> None:
        """Legacy method - connect and get basic info."""
        await self.connect()

    # Event handlers for entities
    def add_status_handler(self, handler) -> None:
        """Add status update handler."""
        self._device.add_status_handler(handler)

    def add_profile_handler(self, handler) -> None:
        """Add profile update handler."""
        self._device.add_profile_handler(handler)

    def add_statistics_handler(self, handler) -> None:
        """Add statistics update handler."""
        self._device.add_statistics_handler(handler)
