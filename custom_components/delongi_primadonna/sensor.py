from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DelongiPrimadonnaOnSensor()
    ])
    return True


class DelongiPrimadonnaOnSensor(SensorEntity):
    def __init__(self):
        pass
