"""Device tracker entity for Delonghi Primadonna."""

from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity_base import DelonghiDeviceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Set up a device tracker for a config entry."""

    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([DelongiPrimadonnaDeviceTracker(delongh_device, hass)])
    return True


class DelongiPrimadonnaDeviceTracker(DelonghiDeviceEntity, ScannerEntity):
    """Implementation of a Delonghi Primadonna device tracker"""
    _attr_name = None

    @property
    def icon(self) -> str:
        """Return the icon of the device."""
        if self.device.switches.is_on:
            return 'mdi:coffee-maker-check'
        if self.device.connected:
            return 'mdi:coffee-maker-check-outline'
        return 'mdi:coffee-maker-outline'

    @property
    def mac_address(self) -> str:
        """Return the mac address of the device."""
        return self.device.mac

    @property
    def hostname(self) -> str:
        """Return the hostname of the device."""
        return self.device.hostname

    @property
    def source_type(self) -> str:
        """Return the source type, eg gps or router, of the device."""
        return 'router'

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        return self.device.connected

    async def async_update(self):
        """Updates the device status"""
        self.hass.async_create_task(self.device.get_device_name())
