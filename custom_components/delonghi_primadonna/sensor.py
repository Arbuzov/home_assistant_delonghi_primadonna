from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import AvailableBeverage, DelonghiDeviceEntity


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DelongiPrimadonnaNozzleSensor(delongh_device, hass),
        DelongiPrimadonnaCookingSensor(delongh_device, hass),
    ])
    return True


class DelongiPrimadonnaNozzleSensor(DelonghiDeviceEntity, SensorEntity):

    _attr_state_class = SensorDeviceClass.ENUM
    _attr_name = 'Nozzle'

    @property
    def native_value(self):
        return self.device.steam_nozzle

    @property
    def icon(self):
        result = 'mdi:coffee'
        if self.device.steam_nozzle == 'DETACHED':
            result = 'mdi:coffee-off-outline'
        if self.device.steam_nozzle == 'MILK':
            result = 'mdi:coffee-outline'
        return result


class DelongiPrimadonnaCookingSensor(DelonghiDeviceEntity, SensorEntity):

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_name = 'Cooking'

    @property
    def native_value(self):
        return self.device.cooking

    @property
    def icon(self):
        result = 'mdi:coffee-to-go'
        if self.device.cooking == AvailableBeverage.NONE:
            result = 'mdi:coffee'
        return result
