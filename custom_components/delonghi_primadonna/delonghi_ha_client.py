"""Home Assistant integrated client for Delonghi PrimaDonna.

This client combines the pure device layer with Home Assistant specific features
like events, notifications, and state management.
"""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.const import CONF_MAC, CONF_MODEL, CONF_NAME
from homeassistant.core import HomeAssistant

from .device import DelonghiPrimaDonnaClient, DeviceStatus
from .ha_bridge import HomeAssistantBridge

_LOGGER = logging.getLogger(__name__)


class DelonghiPrimaDonnaHAClient:
    """Home Assistant integrated client for Delonghi PrimaDonna coffee machines.
    
    This client wraps the pure device client and adds HA-specific features:
    - Events and notifications
    - State persistence  
    - Entity integration
    """

    def __init__(self, config: dict, hass: HomeAssistant) -> None:
        """Initialize the HA client."""
        self._device_client = DelonghiPrimaDonnaClient(config, hass)
        self._ha_bridge = HomeAssistantBridge(
            device=self._device_client._device,
            hass=hass,
            device_name=config.get(CONF_NAME, "PrimaDonna"),
            enable_notifications=False,  # Can be made configurable
        )

    # Delegate device operations to the pure client
    async def connect(self) -> None:
        """Connect to the device."""
        await self._device_client.connect()

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        await self._device_client.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._device_client.is_connected

    @property
    def current_status(self) -> DeviceStatus | None:
        """Get current device status."""
        return self._device_client.current_status

    @property
    def profiles(self) -> dict[int, str]:
        """Get available profiles."""
        return self._device_client.profiles

    @property
    def statistics(self) -> list[int]:
        """Get current statistics."""
        return self._device_client.statistics

    @property
    def mac(self) -> str:
        """Get device MAC address."""
        return self._device_client.mac

    @property 
    def name(self) -> str:
        """Get device name."""
        return self._device_client.name

    @property
    def product_code(self) -> str:
        """Get product code."""
        return self._device_client.product_code

    # Device operations
    async def power_on(self) -> None:
        """Turn on the device."""
        await self._device_client.power_on()

    async def set_profile(self, profile_id: int) -> None:
        """Set active profile."""
        await self._device_client.set_profile(profile_id)

    async def set_time(self, dt: datetime) -> None:
        """Set device clock."""
        await self._device_client.set_time(dt)

    # Additional device commands
    async def cup_light_on(self) -> None:
        """Turn cup light on."""
        # TODO: implement with proper command
        pass

    async def cup_light_off(self) -> None:
        """Turn cup light off."""
        # TODO: implement with proper command  
        pass

    async def energy_save_on(self) -> None:
        """Enable energy save mode."""
        # TODO: implement with proper command
        pass

    async def energy_save_off(self) -> None:
        """Disable energy save mode."""
        # TODO: implement with proper command
        pass

    async def sound_alarm_on(self) -> None:
        """Enable sound alarms."""
        # TODO: implement with proper command
        pass

    async def sound_alarm_off(self) -> None:
        """Disable sound alarms."""
        # TODO: implement with proper command
        pass

    async def select_profile(self, profile_id: int) -> None:
        """Select device profile."""
        await self.set_profile(profile_id)

    async def beverage_start(self, beverage) -> None:
        """Start beverage preparation."""
        # TODO: implement with proper command
        pass

    async def set_auto_power_off(self, interval: int) -> None:
        """Set auto power off interval."""
        # TODO: implement with proper command
        pass

    async def set_water_hardness(self, level: int) -> None:
        """Set water hardness level."""
        # TODO: implement with proper command
        pass

    async def set_water_temperature(self, level: int) -> None:
        """Set water temperature level."""
        # TODO: implement with proper command
        pass

    async def common_command(self, command: str) -> None:
        """Send common command."""
        # TODO: implement with proper command parsing
        pass

    async def request_statistics(self) -> None:
        """Request device statistics."""
        await self._device_client.request_statistics()

    # Legacy device state properties (computed from current_status)
    @property
    def steam_nozzle(self) -> str:
        """Get steam nozzle state."""
        status = self.current_status
        if status:
            from .models import NOZZLE_STATE
            return NOZZLE_STATE.get(status.nozzle_state, str(status.nozzle_state))
        return "unknown"

    @property  
    def status(self) -> str:
        """Get device status."""
        device_status = self.current_status
        if device_status:
            from .models import DEVICE_STATUS
            return DEVICE_STATUS.get(device_status.device_status, "unknown")
        return "unknown"

    @property
    def active_alarms(self) -> list:
        """Get active alarms."""
        status = self.current_status
        if status:
            from .const import ALARM_BIT_MAP, MachineAlarm
            alarms = []
            for bit in status.alarms:
                alarm = ALARM_BIT_MAP.get(bit, MachineAlarm.UNKNOWN)
                if alarm not in (
                    MachineAlarm.IGNORE,
                    MachineAlarm.WATER_SPOUT, 
                    MachineAlarm.IFD_CARAFFE,
                    MachineAlarm.CIOCCO_TANK,
                    MachineAlarm.UNKNOWN,
                ):
                    alarms.append(alarm)
            return alarms
        return []

    @property
    def service(self) -> int:
        """Get service counter."""
        status = self.current_status
        return status.service_counter if status else 0

    @property
    def connected(self) -> bool:
        """Check if device is connected."""
        return self.is_connected

    # Legacy state management (TODO: implement properly)
    @property
    def switches(self):
        """Get device switches state."""
        # This needs to be implemented based on your DeviceSwitches model
        from .models import DeviceSwitches
        return DeviceSwitches()

    @property
    def hostname(self) -> str:
        """Get device hostname."""
        return getattr(self._device_client, '_hostname', self.name)

    @property
    def time_sync(self) -> bool:
        """Get time sync state."""
        return getattr(self, '_time_sync', False)

    @time_sync.setter  
    def time_sync(self, value: bool) -> None:
        """Set time sync state."""
        self._time_sync = value

    @property
    def notify(self) -> bool:
        """Get notification state."""
        return self._ha_bridge._enable_notifications

    @notify.setter
    def notify(self, value: bool) -> None:
        """Set notification state."""
        self._ha_bridge._enable_notifications = value

    # Legacy compatibility
    async def get_device_name(self) -> None:
        """Legacy method - connect and get basic info."""
        await self.connect()

    # HA-specific features
    def enable_notifications(self, enable: bool = True) -> None:
        """Enable/disable HA notifications."""
        self._ha_bridge._enable_notifications = enable

    def fire_raw_event(self, raw_data: bytes) -> None:
        """Fire raw event for debugging."""
        self._ha_bridge.fire_raw_event(raw_data)

    # Event handlers for entities
    def add_status_handler(self, handler) -> None:
        """Add status update handler."""
        self._device_client.add_status_handler(handler)

    def add_profile_handler(self, handler) -> None:
        """Add profile update handler."""
        self._device_client.add_profile_handler(handler)

    def add_statistics_handler(self, handler) -> None:
        """Add statistics update handler."""
        self._device_client.add_statistics_handler(handler)
