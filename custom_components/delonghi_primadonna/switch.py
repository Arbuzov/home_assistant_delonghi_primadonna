from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import DelonghiDeviceEntity


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DelongiPrimadonnaCupLightSwitch(delongh_device)
    ])
    return True


class DelongiPrimadonnaCupLightSwitch(DelonghiDeviceEntity, ToggleEntity):

    _attr_name = 'Cups light'
    _attr_is_on = False

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self.device.cup_light_on()
        self._attr_is_on = True

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self.device.cup_light_off()
        self._attr_is_on = False
