"""Home Assistant integration bridge for Delonghi device.

This module handles the integration between the pure device logic
and Home Assistant specific concerns like events, notifications, and state.
"""

from __future__ import annotations

import logging
import uuid
from binascii import hexlify

from homeassistant.core import HomeAssistant

from .const import DOMAIN, ALARM_BIT_MAP, MachineAlarm
from .device.delonghi_device import DelonghiDevice
from .device.message_parser import DeviceStatus
from .models import DEVICE_NOTIFICATION

_LOGGER = logging.getLogger(__name__)


class HomeAssistantBridge:
    """Bridge between DelonghiDevice and Home Assistant."""

    def __init__(
        self, 
        device: DelonghiDevice, 
        hass: HomeAssistant,
        device_name: str,
        enable_notifications: bool = False
    ) -> None:
        """Initialize the bridge."""
        self._device = device
        self._hass = hass
        self._device_name = device_name
        self._enable_notifications = enable_notifications
        
        # Wire up device events to HA
        self._device.add_status_handler(self._handle_status_update)
        self._device.add_profile_handler(self._handle_profile_update)
        self._device.add_statistics_handler(self._handle_statistics_update)

    def _handle_status_update(self, status: DeviceStatus) -> None:
        """Handle device status updates."""
        # Fire HA event
        event_data = {
            "device": self._device.mac_address,
            "status": {
                "powered": status.is_powered,
                "nozzle_state": status.nozzle_state,
                "service_counter": status.service_counter,
                "device_status": status.device_status,
                "alarms": self._convert_alarms(status.alarms),
            }
        }
        
        self._hass.bus.fire(f"{DOMAIN}_status_update", event_data)
        
        # Handle alarms
        if status.alarms:
            self._handle_alarms(status.alarms, status.raw_data)

    def _handle_profile_update(self, profiles: dict[int, str]) -> None:
        """Handle profile updates."""
        event_data = {
            "device": self._device.mac_address,
            "profiles": profiles
        }
        self._hass.bus.fire(f"{DOMAIN}_profiles_update", event_data)

    def _handle_statistics_update(self, statistics: list[int]) -> None:
        """Handle statistics updates."""
        event_data = {
            "device": self._device.mac_address,
            "statistics": statistics
        }
        self._hass.bus.fire(f"{DOMAIN}_statistics", event_data)

    def _convert_alarms(self, alarm_bits: list[int]) -> list[str]:
        """Convert alarm bit positions to alarm names."""
        alarms = []
        for bit in alarm_bits:
            alarm = ALARM_BIT_MAP.get(bit, MachineAlarm.UNKNOWN)
            if alarm not in (
                MachineAlarm.IGNORE,
                MachineAlarm.WATER_SPOUT,
                MachineAlarm.IFD_CARAFFE,
                MachineAlarm.CIOCCO_TANK,
                MachineAlarm.UNKNOWN,
            ):
                alarms.append(alarm.value if hasattr(alarm, 'value') else str(alarm))
        return alarms

    def _handle_alarms(self, alarm_bits: list[int], raw_data: bytes) -> None:
        """Handle alarm notifications."""
        if not self._enable_notifications:
            return

        # Check if this is a known notification
        notification_key = str(bytearray(raw_data))
        if notification_key in DEVICE_NOTIFICATION:
            note = DEVICE_NOTIFICATION[notification_key]
            message = note.description
        else:
            # Format as hex for unknown messages
            message = (
                str(hexlify(raw_data, " "))
                .replace(" ", ", 0x")
                .replace("b'", "[0x")
                .replace("'", "]")
            )

        # Create persistent notification
        self._hass.services.call(
            "persistent_notification",
            "create",
            {
                "message": message,
                "title": f"{self._device_name} Alert",
                "notification_id": f"{self._device.mac_address}_alarm_{uuid.uuid4()}",
            },
        )

    def fire_raw_event(self, raw_data: bytes) -> None:
        """Fire raw event for debugging/advanced usage."""
        event_data = {
            "device": self._device.mac_address,
            "data": hexlify(raw_data, " ").decode()
        }
        self._hass.bus.fire(f"{DOMAIN}_raw_event", event_data)
