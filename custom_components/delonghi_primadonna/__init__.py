"""Delonghi integration"""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import BEVERAGE_SERVICE_NAME, DOMAIN
from .device import AvailableBeverage, BeverageEntityFeature, DelongiPrimadonna

PLATFORMS: list[str] = [
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.TEXT,
    Platform.DEVICE_TRACKER,
]

__all__ = ['async_setup_entry', 'async_unload_entry', 'BeverageEntityFeature']

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry"""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    delonghi_device = DelongiPrimadonna(entry.data, hass)
    hass.data[DOMAIN][entry.unique_id] = delonghi_device
    _LOGGER.debug('Device id %s', entry.unique_id)

    hass.async_create_task(delonghi_device.get_device_name())
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def make_beverage(call: ServiceCall) -> None:
        _LOGGER.debug('Make beverage %s', call.data)
        await delonghi_device.beverage_start(call.data['beverage'])

    hass.services.async_register(
        DOMAIN,
        BEVERAGE_SERVICE_NAME,
        make_beverage,
        schema=vol.Schema(
            {
                vol.Required('beverage'): vol.In([*AvailableBeverage]),
                vol.Optional('entity_id'): vol.Coerce(str),
                vol.Optional('device_id'): vol.Coerce(str),
            }
        ),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        await hass.data[DOMAIN][entry.unique_id].disconnect()
        hass.data[DOMAIN].pop(entry.unique_id)
    _LOGGER.debug('Unload %s', entry.unique_id)
    return unload_ok
