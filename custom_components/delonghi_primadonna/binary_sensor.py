from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
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
        DelongiPrimadonnaCookingSensor(delongh_device)
    ])
    return True


class DelongiPrimadonnaCookingSensor(DelonghiDeviceEntity, BinarySensorEntity):

    _attr_device_class = BinarySensorDeviceClass.HEAT
    _attr_name = 'Cooking'

    @property
    def is_on(self):
        return self.device.cooking != AvailableBeverage.NONE
