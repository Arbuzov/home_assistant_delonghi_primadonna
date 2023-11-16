import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import AVAILABLE_PROFILES, DOMAIN, POWER_OFF_OPTIONS
from .device import (AvailableBeverage, BeverageEntityFeature,
                     DelonghiDeviceEntity, DelongiPrimadonna)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    delongh_device: DelongiPrimadonna = hass.data[DOMAIN][entry.unique_id]
    async_add_entities(
        [
            BeverageSelect(delongh_device, hass),
            EnergySaveModeSelect(delongh_device, hass),
            ProfileSelect(delongh_device, hass),
            WaterHardnessSelect(delongh_device, hass),
            WaterTemperatureSelect(delongh_device, hass)
        ]
    )
    return True


class ProfileSelect(DelonghiDeviceEntity, SelectEntity):
    """Implementation for profile selection."""

    _attr_options = list(AVAILABLE_PROFILES.keys())
    _attr_current_option = list(AVAILABLE_PROFILES.keys())[0]
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = 'profile'
    _attr_icon = 'mdi:account'

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.CONFIG

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        profile_id = AVAILABLE_PROFILES.get(option)
        self.hass.async_create_task(self.device.select_profile(profile_id))
        self._attr_current_option = option


class BeverageSelect(DelonghiDeviceEntity, SelectEntity):
    """Beverage start implementation by the select"""

    _attr_options = [*AvailableBeverage]
    _attr_current_option = [*AvailableBeverage][0]
    _attr_translation_key = 'make_beverage'
    _attr_icon = 'mdi:coffee'
    _attr_supported_features: BeverageEntityFeature \
        = BeverageEntityFeature.MAKE_BEVERAGE

    async def async_select_option(self, option: str) -> None:
        """Select beverage action"""
        self.hass.async_create_task(self.device.beverage_start(option))


class EnergySaveModeSelect(DelonghiDeviceEntity, SelectEntity):
    """Energy save mode management"""

    _attr_options = list(POWER_OFF_OPTIONS.keys())
    _attr_current_option = list(POWER_OFF_OPTIONS.keys())[3]
    _attr_translation_key = 'energy_save_mode'
    _attr_icon = 'mdi:power-plug-off'

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.CONFIG

    async def async_select_option(self, option: str) -> None:
        """Select energy save mode action"""
        power_off_interval = POWER_OFF_OPTIONS.get(option)
        self.hass.async_create_task(
            self.device.set_auto_power_off(power_off_interval)
        )
        self._attr_current_option = option


class WaterHardnessSelect(DelonghiDeviceEntity, SelectEntity):
    """Water hardness management"""

    _attr_options = ['Soft', 'Medium', 'Hard', 'Very Hard']
    _attr_current_option = 'Soft'
    _attr_translation_key = 'water_hardness'
    _attr_icon = 'mdi:water'

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.CONFIG

    async def async_select_option(self, option: str) -> None:
        """Select water hardness action"""
        water_hardness = self._attr_options.index(option)
        self.hass.async_create_task(
            self.device.set_water_hardness(water_hardness)
        )
        self._attr_current_option = option


class WaterTemperatureSelect(DelonghiDeviceEntity, SelectEntity):
    """Water temperature management"""

    _attr_options = ['Low', 'Medium', 'High', 'Highest']
    _attr_current_option = 'Low'
    _attr_translation_key = 'water_temperature'
    _attr_icon = 'mdi:thermometer'
    _attr_supported_features: BeverageEntityFeature = BeverageEntityFeature(1)

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.CONFIG

    async def async_select_option(self, option: str) -> None:
        """Select water temperature action"""
        water_temperature = self._attr_options.index(option)
        self.hass.async_create_task(
            self.device.set_water_temperature(water_temperature)
        )
        self._attr_current_option = option
