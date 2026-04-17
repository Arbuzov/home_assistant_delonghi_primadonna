"""Sensor entities for Delonghi Primadonna."""

from typing import Any

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .base_entity import DelonghiDeviceEntity
from .const import DOMAIN
from .device import NOZZLE_STATE, DelongiPrimadonna
from .machine_switch import MachineSwitch


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Register sensor entities for a config entry."""

    delongh_device: DelongiPrimadonna = hass.data[DOMAIN][entry.unique_id]
    async_add_entities(
        [
            DelongiPrimadonnaNozzleSensor(delongh_device, hass),
            DelongiPrimadonnaStatusSensor(delongh_device, hass),
            DelongiPrimadonnaSwitchesSensor(delongh_device, hass),

            # Statistics sensors
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'total_coffee',
                -3077, 'Total Coffee', icon='mdi:coffee',
            ),
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'total_coffee_with_milk',
                -3001, 'Total Coffee with Milk',
                icon='mdi:coffee-outline',
            ),
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'total_water',
                10106, 'Total Water', 'L', 'mdi:water',
            ),
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'descaling_count',
                105, 'Descaling Count', icon='mdi:shimmer',
            ),
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'milk_cleaning_count',
                115, 'Milk Cleaning Count',
                icon='mdi:water-sync',
            ),
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'filter_replace_count',
                108, 'Filter Replacements', icon='mdi:filter',
            ),
        ]
    )

    hass.async_create_task(delongh_device.update_statistics())
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
        if self.device.steam_nozzle == "milk_frother":
            result = 'mdi:coffee-outline'
        return result


class DelongiPrimadonnaStatusSensor(
    DelonghiDeviceEntity, SensorEntity, RestoreEntity
):
    """
    Shows the actual device status
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = 'device_status'

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
        if self.device.status == "Ready":
            return 'mdi:thumb-up-outline'
        return 'mdi:alert-circle-outline'


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


class DelongiPrimadonnaStatisticsSensor(
    DelonghiDeviceEntity, SensorEntity, RestoreEntity
):
    """
    Shows statistics from the machine.
    """

    _attr_device_class = None
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        device: DelongiPrimadonna,
        hass: HomeAssistant,
        sensor_type: str,
        param_id: int,
        name: str,
        native_unit_of_measurement: str = None,
        icon: str = 'mdi:counter'
    ) -> None:
        """Initialize the sensor."""
        super().__init__(device, hass)
        self._param_id = param_id
        self._attr_name = name
        self._attr_unique_id = (
            f"{device.mac}_{sensor_type}"
        )
        self._attr_translation_key = sensor_type
        self._attr_native_unit_of_measurement = (
            native_unit_of_measurement
        )
        self._attr_icon = icon

    async def async_added_to_hass(self) -> None:
        """Restore last known numeric state."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        value = last_state.state
        if value in (None, "", "unknown", "unavailable"):
            return
        try:
            self._attr_native_value = float(value)
        except (TypeError, ValueError):
            return

    @property
    def native_value(self):
        """Return current value, or restored value as fallback."""
        val = self.device.statistics.get(self._param_id)
        if val is not None:
            return val
        return self._attr_native_value

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._attr_icon

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        if self.device.connected:
            self.hass.async_create_task(
                self.device.update_statistics()
            )
