"""Delonghi integration"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import voluptuous as vol
from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import BEVERAGE_SERVICE_NAME, DOMAIN
from .device import AvailableBeverage, BeverageEntityFeature, DelongiPrimadonna

PLATFORMS: list[str] = [
    Platform.IMAGE,
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
    _LOGGER.debug("Device data %s", entry.data)
    hass.async_create_task(delonghi_device.get_device_name())
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Automatically load the Lovelace card
    card_name = "DelonghiPrimadonna.js"
    hacs_path = hass.config.path(
        f"www/community/{DOMAIN}/{card_name}"
    )
    local_card = Path(__file__).parents[1] / "dist" / card_name

    hacs_exists = await hass.async_add_executor_job(os.path.isfile, hacs_path)
    local_exists = await hass.async_add_executor_job(os.path.isfile, str(local_card))

    if hacs_exists:
        card_url = f"/hacsfiles/{DOMAIN}/{card_name}"
        frontend.add_extra_js_url(hass, card_url, es5=True)
        _LOGGER.debug("Registered Lovelace card from HACS path: %s", hacs_path)
    elif local_exists:
        card_url = f"/{DOMAIN}/{card_name}"
        await hass.http.async_register_static_paths(
            [StaticPathConfig(card_url, str(local_card), False)]
        )
        frontend.add_extra_js_url(hass, card_url, es5=True)
        _LOGGER.debug("Registered Lovelace card from local dist path: %s", local_card)
    else:
        _LOGGER.error(
            "Lovelace card not found in either HACS path (%s) or local dist path (%s). Card will not be registered.",
            hacs_path, local_card
        )

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


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the Delonghi entry."""

    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
