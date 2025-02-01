from homeassistant.components.binary_sensor import (BinarySensorDeviceClass,
                                                    BinarySensorEntity)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import DelonghiDeviceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities(
        [
            DelongiPrimadonnaDescaleSensor(delongh_device, hass),
            DelongiPrimadonnaFilterSensor(delongh_device, hass),
            DelongiPrimadonnaEnabledSensor(delongh_device, hass),
        ]
    )
    return True


class DelongiPrimadonnaEnabledSensor(DelonghiDeviceEntity, BinarySensorEntity):
    """
    Shows if the device up and running
    """

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = 'Enabled'

    @property
    def icon(self) -> str:
        """Return the icon of the device."""
        if self.device.switches.is_on:
            return 'mdi:coffee-maker-check'
        if self.device.connected:
            return 'mdi:coffee-maker-check-outline'
        return 'mdi:coffee-maker-outline'

    @property
    def native_value(self):
        return self.device.switches.is_on

    @property
    def is_on(self) -> bool:
        return self.device.switches.is_on


class DelongiPrimadonnaDescaleSensor(DelonghiDeviceEntity, BinarySensorEntity):
    """
    Shows if the device needs descaling
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = 'Descaling'

    @property
    def native_value(self):
        return self.device.service

    @property
    def is_on(self) -> bool:
        return bool((self.device.service >> 2) % 2)

    @property
    def icon(self):
        result = 'mdi:dishwasher'
        if self.is_on:
            result = 'mdi:dishwasher-alert'
        return result


class DelongiPrimadonnaFilterSensor(DelonghiDeviceEntity, BinarySensorEntity):
    """
    Shows if the filter need to be changed
    """

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = 'Filter'

    @property
    def native_value(self):
        return self.device.service

    @property
    def is_on(self) -> bool:
        return bool((self.device.service >> 3) % 2)

    @property
    def icon(self):
        result = 'mdi:filter'
        if self.is_on:
            result = 'mdi:filter-off'
        return result
