from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DelongiPrimadonnaPowerSwitch(delongh_device),
        DelongiPrimadonnaCupLightSwitch(delongh_device)
    ])
    return True


class DelongiPrimadonnaPowerSwitch(ToggleEntity):

    _attr_is_on = STATE_OFF
    _attr_name = "Power switch"

    def __init__(self, delongh_device):
        self._attr_is_on = STATE_ON
        self._attr_unique_id = f"{delongh_device.mac}_power"
        self.device = delongh_device

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self.device.turn_on()
        self._attr_is_on = STATE_ON

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self.device.turn_off()
        self._attr_is_on = STATE_OFF

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }


class DelongiPrimadonnaCupLightSwitch(ToggleEntity):

    _attr_name = "Cups light"

    def __init__(self, delongh_device):
        self._attr_is_on = False
        self._attr_unique_id = f"{delongh_device.mac}_cup_light"
        self.device = delongh_device

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self.device.cup_light_on()
        self._attr_is_on = True

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self.device.cup_light_off()
        self._attr_is_on = False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }
