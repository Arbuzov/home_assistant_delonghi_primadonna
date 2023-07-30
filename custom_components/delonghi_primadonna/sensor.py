from homeassistant.components.binary_sensor import (BinarySensorDeviceClass,
                                                    BinarySensorEntity)
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import (DEVICE_STATUS, NOZZLE_STATE, SERVICE_STATE,
                     DelonghiDeviceEntity)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DelongiPrimadonnaNozzleSensor(delongh_device, hass),
        DelongiPrimadonnaDescaleSensor(delongh_device, hass),
        DelongiPrimadonnaFilterSensor(delongh_device, hass),
        DelongiPrimadonnaStatusSensor(delongh_device, hass),
    ])
    return True


class DelongiPrimadonnaNozzleSensor(DelonghiDeviceEntity, SensorEntity):
    """
    Check the connected steam nozzle
    Steam or milk pot
    """
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_name = 'Nozzle'

    _attr_options = list(NOZZLE_STATE.values())

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


class DelongiPrimadonnaStatusSensor(DelonghiDeviceEntity, SensorEntity):
    """
    Shows the actual device status
    """
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_name = 'Status'
    _attr_options = list(DEVICE_STATUS.values())

    @property
    def native_value(self):
        return self.device.status

    @property
    def icon(self):
        result = 'mdi:thumb-up-outline'
        return result


class DelongiPrimadonnaDescaleSensor(DelonghiDeviceEntity, BinarySensorEntity):
    """
    Checks if the device need some service maintenance
    Change filter or descale
    """
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = 'Service'
    _attr_options = list(SERVICE_STATE.values())

    @property
    def native_value(self):
        return self.device.service

    @property
    def is_on(self) -> bool:
        return bool((self.device.service >> 3) % 2)

    @property
    def icon(self):
        result = 'mdi:dishwasher'
        if self.is_on():
            result = 'mdi:dishwasher-alert'
        return result


class DelongiPrimadonnaFilterSensor(
        DelonghiDeviceEntity,
        BinarySensorEntity):
    """
    Checks if the device need some service maintenance
    Change filter or descale
    """
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = 'Service'
    _attr_options = list(SERVICE_STATE.values())

    @property
    def native_value(self):
        return self.device.service

    @property
    def is_on(self) -> bool:
        return bool((self.device.service >> 4) % 2)

    @property
    def icon(self):
        result = 'mdi:filter'
        if self.is_on():
            result = 'mdi:filter-off'
        return result
