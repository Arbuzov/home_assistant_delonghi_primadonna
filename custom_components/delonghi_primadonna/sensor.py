from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import DEVICE_STATUS, NOZZLE_STATE, DelonghiDeviceEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities(
        [
            DelongiPrimadonnaNozzleSensor(delongh_device, hass),
            DelongiPrimadonnaStatusSensor(delongh_device, hass),
        ]
    )
    return True


class DelongiPrimadonnaNozzleSensor(DelonghiDeviceEntity, SensorEntity):
    """
    Check the connected steam nozzle
    Steam or milk pot
    """

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_name = "Nozzle"

    _attr_options = list(NOZZLE_STATE.values())

    @property
    def native_value(self):
        return self.device.steam_nozzle

    @property
    def icon(self):
        result = "mdi:coffee"
        if self.device.steam_nozzle == "DETACHED":
            result = "mdi:coffee-off-outline"
        if self.device.steam_nozzle == "MILK":
            result = "mdi:coffee-outline"
        return result


class DelongiPrimadonnaStatusSensor(DelonghiDeviceEntity, SensorEntity):
    """
    Shows the actual device status
    """

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_name = "Status"
    _attr_options = list(DEVICE_STATUS.values())

    @property
    def native_value(self):
        return self.device.status

    @property
    def icon(self):
        result = "mdi:thumb-up-outline"
        return result
