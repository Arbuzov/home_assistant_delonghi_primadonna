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

__all__ = [
    'async_setup_entry',
    'async_unload_entry',
    'BeverageEntityFeature'
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up oiot from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    delonghi_device = DelongiPrimadonna(entry.data, hass)
    hass.data[DOMAIN][entry.unique_id] = delonghi_device
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def make_beverage(call: ServiceCall) -> None:
        await delonghi_device.beverage_start(call.data['beverage'])

    hass.services.async_register(
        DOMAIN,
        BEVERAGE_SERVICE_NAME,
        make_beverage,
        schema=vol.Schema({
            vol.Required('beverage'): vol.In([*AvailableBeverage]),
        })
        [BeverageEntityFeature.MAKE_BEVERAGE]
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS
    )
    if unload_ok:
        await hass.data[DOMAIN][entry.unique_id].disconnect()
        hass.data[DOMAIN].pop(entry.unique_id)
    _LOGGER.info('Unload %s', entry.unique_id)
    return unload_ok
