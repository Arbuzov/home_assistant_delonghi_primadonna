"""Image entity for Delonghi Primadonna."""

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base_entity import DelonghiDeviceEntity
from .const import DEFAULT_IMAGE_URL, DOMAIN
from .device import DelongiPrimadonna
from .model import get_machine_model


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

    def __init__(
        self, delongh_device: DelongiPrimadonna, hass: HomeAssistant
    ) -> None:
        """Initialize the image entity."""
        DelonghiDeviceEntity.__init__(self, delongh_device, hass)
        ImageEntity.__init__(self, hass)
        model = get_machine_model(delongh_device.product_code)
        if model is not None and model.image_url:
            self._attr_image_url = model.image_url
