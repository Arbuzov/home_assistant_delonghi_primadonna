"""Delonghi integration"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .device import DelongiPrimadonna

PLATFORMS: list[str] = [Platform.SWITCH, Platform.BUTTON,
                        Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up oiot from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    delonghi_device = DelongiPrimadonna(entry.data, hass)
    hass.data[DOMAIN][entry.unique_id] = delonghi_device
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.unique_id)

    return unload_ok
