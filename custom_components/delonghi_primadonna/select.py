import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN, AVAILABLE_PROFILES
from .device import DelonghiDeviceEntity, DelongiPrimadonna

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    delongh_device: DelongiPrimadonna = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        ProfileSelect(delongh_device, hass)
    ])
    return True


class ProfileSelect(DelonghiDeviceEntity, SelectEntity):
    """A select implementation for profile selection."""

    def __init__(self, delongh_device, hass: HomeAssistant) -> None:
        super().__init__(delongh_device, hass)
        _LOGGER.info("Create Select Entity")
        self.selected_option = AVAILABLE_PROFILES.keys()[0]

    @property
    def name(self):
        """Name of the entity."""
        return "Profile"

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        return AVAILABLE_PROFILES.keys()

    @property
    def current_option(self) -> str:
        """Return the state of the entity."""
        return self.selected_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        profile_id = AVAILABLE_PROFILES.get(option)
        self.hass.async_create_task(self.device.select_profile(profile_id))
        self.selected_option = option