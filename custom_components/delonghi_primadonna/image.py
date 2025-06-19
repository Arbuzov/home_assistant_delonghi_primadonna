"""Image entity for Delonghi Primadonna."""

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEFAULT_IMAGE_URL, DOMAIN
from .device import DelonghiDeviceEntity, DelongiPrimadonna


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up image entity for a config entry."""

    delongh_device: DelongiPrimadonna = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([DelongiPrimadonnaImage(delongh_device, hass)])
    return True


class DelongiPrimadonnaImage(DelonghiDeviceEntity, ImageEntity):
    """Image entity showing a picture of the device."""

    _attr_image_url = DEFAULT_IMAGE_URL
    _attr_name = "Image"

    def __init__(self, delongh_device: DelongiPrimadonna, hass: HomeAssistant):
        """Initialize the image entity."""
        DelonghiDeviceEntity.__init__(self, delongh_device, hass)
        ImageEntity.__init__(self)
