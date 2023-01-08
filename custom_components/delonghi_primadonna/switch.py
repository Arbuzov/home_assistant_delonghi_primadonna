from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import DelonghiDeviceEntity


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DelongiPrimadonnaCupLightSwitch(delongh_device, hass),
        DelongiPrimadonnaNotificationSwitch(delongh_device, hass)
    ])
    return True


class DelongiPrimadonnaCupLightSwitch(DelonghiDeviceEntity, ToggleEntity):

    _attr_name = 'Cups light'
    _attr_is_on = False
    _attr_icon = 'mdi:lightbulb'

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self.hass.async_create_task(self.device.cup_light_on())
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self.hass.async_create_task(self.device.cup_light_off())
        self._attr_is_on = False


class DelongiPrimadonnaNotificationSwitch(DelonghiDeviceEntity, ToggleEntity):
    """This switch enable HA side bar notification on device status change"""

    _attr_name = 'Enable notification'
    _attr_icon = 'mdi:magnify-expand'

    @property
    def is_on(self, **kwargs: Any) -> None:
        """Checks is the notification ON."""
        return self.device.notify

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the notification on."""
        self.device.notify = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the notification off."""
        self.device.notify = False
