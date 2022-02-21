from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DelongiPrimadonnaLongButton(delongh_device),
        DelongiPrimadonnaCoffeeButton(delongh_device),
        DelongiPrimadonnaDopioButton(delongh_device),
        DelongiPrimadonnaSteamButton(delongh_device),
        DelongiPrimadonnaHotWaterButton(delongh_device),
        DelongiPrimadonnaEspresso2Button(delongh_device),
        DelongiPrimadonnaAmericanoButton(delongh_device),
        DelongiPrimadonnaEspressoButton(delongh_device),
        DelongiPrimadonnaCancelButton(delongh_device)
    ])
    return True


class DelongiPrimadonnaLongButton(ButtonEntity):

    _attr_name = "Prepare long"

    def __init__(self, delongh_device):
        self._attr_unique_id = f"{delongh_device.mac}_long"
        self.device = delongh_device

    def press(self):
        self.device.coffe_long_start()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }


class DelongiPrimadonnaCoffeeButton(ButtonEntity):

    _attr_name = "Prepare Coffee"

    def __init__(self, delongh_device):
        self._attr_unique_id = f"{delongh_device.mac}_coffe"
        self.device = delongh_device

    def press(self):
        self.device.coffe_long_start()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }


class DelongiPrimadonnaDopioButton(ButtonEntity):

    _attr_name = "Prepare Doppio+"

    def __init__(self, delongh_device):
        self._attr_unique_id = f"{delongh_device.mac}_dopio"
        self.device = delongh_device

    def press(self):
        self.device.coffe_long_start()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }


class DelongiPrimadonnaSteamButton(ButtonEntity):

    _attr_name = "Prepare Steam"

    def __init__(self, delongh_device):
        self._attr_unique_id = f"{delongh_device.mac}_steam"
        self.device = delongh_device

    def press(self):
        self.device.coffe_long_start()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }


class DelongiPrimadonnaHotWaterButton(ButtonEntity):

    _attr_name = "Prepare Hot Water"

    def __init__(self, delongh_device):
        self._attr_unique_id = f"{delongh_device.mac}_hot_water"
        self.device = delongh_device

    def press(self):
        self.device.coffe_long_start()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }


class DelongiPrimadonnaEspresso2Button(ButtonEntity):

    _attr_name = "Prepare x2 Espresso"

    def __init__(self, delongh_device):
        self._attr_unique_id = f"{delongh_device.mac}_espresso2"
        self.device = delongh_device

    def press(self):
        self.device.coffe_long_start()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }


class DelongiPrimadonnaAmericanoButton(ButtonEntity):

    _attr_name = "Prepare Americano"

    def __init__(self, delongh_device):
        self._attr_unique_id = f"{delongh_device.mac}_americano"
        self.device = delongh_device

    def press(self):
        self.device.coffe_long_start()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }


class DelongiPrimadonnaEspressoButton(ButtonEntity):

    _attr_name = "Prepare Espresso"

    def __init__(self, delongh_device):
        self._attr_unique_id = f"{delongh_device.mac}_espresso"
        self.device = delongh_device

    def press(self):
        self.device.coffe_long_start()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }


class DelongiPrimadonnaCancelButton(ButtonEntity):

    _attr_name = "Cancel cooking"

    def __init__(self, delongh_device):
        self._attr_unique_id = f"{delongh_device.mac}_cancel"
        self.device = delongh_device

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.mac)},
            "connections": {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            "name": self.device.name,
            "manufacturer": "Delongi",
            "model": self.device.model
        }
