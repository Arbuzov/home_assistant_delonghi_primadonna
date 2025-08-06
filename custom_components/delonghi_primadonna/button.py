"""Button entity definitions for Delonghi Primadonna."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import DelonghiDeviceEntity, DelongiPrimadonna


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Set up button entities for a config entry."""

    delongh_device: DelongiPrimadonna = hass.data[DOMAIN][entry.unique_id]
    async_add_entities(
        [
            DelongiPrimadonnaPowerButton(delongh_device, hass),
            DelongiPrimadonnaStatisticsButton(delongh_device, hass),
        ]
    )
    return True


class DelongiPrimadonnaPowerButton(DelonghiDeviceEntity, ButtonEntity):
    """This button turns on the device"""

    _attr_translation_key = 'power_on'

    async def async_press(self):
        self.hass.async_create_task(self.device.power_on())


class DelongiPrimadonnaStatisticsButton(DelonghiDeviceEntity, ButtonEntity):
    """Button to read device statistics."""

    _attr_translation_key = "statistics"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        """Return if entity is available (debug mode only)."""
        return super().available and self.device.notify

    async def async_press(self) -> None:
        """Fetch statistics from the device and log them."""
        try:
            stats = await self.device.read_statistics()
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Failed to read statistics: %s", err)
            return
        _LOGGER.debug("Machine statistics: %s", stats)
