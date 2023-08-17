"""Delonghi integration"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .device import DelongiPrimadonna

PLATFORMS: list[str] = [Platform.BUTTON,
                        Platform.BINARY_SENSOR,
                        Platform.SENSOR,
                        Platform.SELECT,
                        Platform.SWITCH,
                        Platform.DEVICE_TRACKER]


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up oiot from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    delonghi_device = DelongiPrimadonna(entry.data, hass)
    hass.data[DOMAIN][entry.unique_id] = delonghi_device
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS)
    if unload_ok:
        await hass.data[DOMAIN][entry.unique_id].disconnect()
        hass.data[DOMAIN].pop(entry.unique_id)
    _LOGGER.info('Unload %s', entry.unique_id)
    return unload_ok
