"""Sensor entities for Delonghi Primadonna."""

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .device import DEVICE_STATUS, NOZZLE_STATE, DelonghiDeviceEntity
from .machine_switch import MachineSwitch


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Register sensor entities for a config entry."""

    delongh_device = hass.data[DOMAIN][entry.unique_id]
    async_add_entities(
        [
            DelongiPrimadonnaNozzleSensor(delongh_device, hass),
            DelongiPrimadonnaStatusSensor(delongh_device, hass),
            DelongiPrimadonnaSwitchesSensor(delongh_device, hass),
        ]
    )
    return True


class DelongiPrimadonnaNozzleSensor(
    DelonghiDeviceEntity, SensorEntity, RestoreEntity
):
    """
    Check the connected steam nozzle
    Steam or milk pot
    """

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = 'nozzle_status'

    _attr_options = list(NOZZLE_STATE.values())

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_native_value = last_state.state

    @property
    def native_value(self):
        return self.device.steam_nozzle

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.DIAGNOSTIC

    @property
    def icon(self):
        result = 'mdi:coffee'
        if self.device.steam_nozzle == "detached":
            result = 'mdi:coffee-off-outline'
        if self.device.steam_nozzle.startswith("milk"):
            result = 'mdi:coffee-outline'
        return result


class DelongiPrimadonnaStatusSensor(
    DelonghiDeviceEntity, SensorEntity, RestoreEntity
):
    """
    Shows the actual device status
    """

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = 'Status'
    _attr_options = list(DEVICE_STATUS.values())

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_native_value = last_state.state

    @property
    def native_value(self):
        return self.device.status

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.DIAGNOSTIC

    @property
    def icon(self):
        result = 'mdi:thumb-up-outline'
        return result


class DelongiPrimadonnaSwitchesSensor(
    DelonghiDeviceEntity, SensorEntity, RestoreEntity
):
    """Show active machine switches."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = 'switches'
    _attr_options = [
        'none',
        *[s.value for s in MachineSwitch if s not in (
            MachineSwitch.IGNORE_SWITCH,
            MachineSwitch.UNKNOWN_SWITCH,
        )],
    ]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_native_value = last_state.state

    @property
    def native_value(self):
        if not self.device.active_switches:
            return 'none'
        return ', '.join(s.value for s in self.device.active_switches)

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.DIAGNOSTIC
