import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import AVAILABLE_PROFILES, DOMAIN
from .device import AvailableBeverage, DelonghiDeviceEntity, DelongiPrimadonna

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    delongh_device: DelongiPrimadonna = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        ProfileSelect(delongh_device, hass),
        BeverageSelect(delongh_device, hass),
        EnergySaveModeSelect(delongh_device, hass)
    ])
    return True


class ProfileSelect(DelonghiDeviceEntity, SelectEntity):
    """Implementation for profile selection."""

    _attr_name = 'Profile'
    _attr_options = list(AVAILABLE_PROFILES.keys())
    _attr_current_option = list(AVAILABLE_PROFILES.keys())[0]

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        profile_id = AVAILABLE_PROFILES.get(option)
        self.hass.async_create_task(self.device.select_profile(profile_id))
        self._attr_current_option = option


class BeverageSelect(DelonghiDeviceEntity, SelectEntity):
    """Beverage start implementation by the select"""

    _attr_name = 'Beverage'
    _attr_options = [*AvailableBeverage]
    _attr_current_option = [*AvailableBeverage][0]

    async def async_select_option(self, option: str) -> None:
        """Select beverage action"""
        self.hass.async_create_task(
            self.device.beverage_start(option))


class EnergySaveModeSelect(DelonghiDeviceEntity, SelectEntity):
    """Energy save mode management"""

    _attr_name = 'Energy Save Mode'
    _attr_options = ['15min', '3h']
    _attr_current_option = '15min'

    async def async_select_option(self, option: str) -> None:
        """Select energy save mode action"""
        _LOGGER.warning('Energy save mode is not implemented yet')
