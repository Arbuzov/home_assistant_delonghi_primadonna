import logging

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import DelonghiDeviceEntity, DelongiPrimadonna

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    delongh_device: DelongiPrimadonna = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DebugInput(delongh_device, hass)
    ])
    return True

class DebugInput(DelonghiDeviceEntity, TextEntity):
    """Implementation debug input."""
    _attr_name = None

    async def async_set_value(self, value: str) -> None:
        await self.device.send_command(value)
        
    @property
    def available(self) -> bool:
        return device.notify
