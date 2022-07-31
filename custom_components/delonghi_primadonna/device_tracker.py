import logging

from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import DelonghiDeviceEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DelongiPrimadonnaDeviceTracker(delongh_device, hass)
    ])
    return True


class DelongiPrimadonnaDeviceTracker(DelonghiDeviceEntity, ScannerEntity):

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
