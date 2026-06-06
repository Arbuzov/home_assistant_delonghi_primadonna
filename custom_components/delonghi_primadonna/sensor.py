"""Sensor entities for Delonghi Primadonna."""

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .base_entity import DelonghiDeviceEntity
from .const import DOMAIN
from .device import DelongiPrimadonna, NOZZLE_STATE
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
                3001, 'Total Coffee with Milk',
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
                111, 'Milk Cleaning Count',
                icon='mdi:water-sync',
            ),
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'filter_replace_count',
                108, 'Filter Replacements', icon='mdi:filter',
            ),
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'total_tea', 3025, 'Total Tea',
                icon='mdi:tea'),
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'total_choco', 3021, 'Total Choco',
                icon='mdi:cup-water'),
            DelongiPrimadonnaStatisticsSensor(
                delongh_device, hass, 'total_cold_milk', 3017,
                'Total Cold Milk', icon='mdi:snowflake'),

            # Utility sensors (Disabled by default)
            DelongiPrimadonnaUtilitySensor(
                delongh_device, hass, 'daily_coffee', -3077, 'Daily Coffee',
                period='daily', icon='mdi:coffee-to-go'),
            DelongiPrimadonnaUtilitySensor(
                delongh_device, hass, 'weekly_coffee', -3077, 'Weekly Coffee',
                period='weekly', icon='mdi:coffee-to-go'),
            DelongiPrimadonnaUtilitySensor(
                delongh_device, hass, 'daily_water', 10106, 'Daily Water',
                'L', period='daily', icon='mdi:water'),
            DelongiPrimadonnaUtilitySensor(
                delongh_device, hass, 'weekly_water', 10106, 'Weekly Water',
                'L', period='weekly', icon='mdi:water'),
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
        if self.device.steam_nozzle == "milk_frother":
            return 'mdi:coffee-outline'
        return 'mdi:coffee'


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
        """Return the current value from the statistics dictionary."""
        return self.device.statistics.get(
            self._param_id, self._attr_native_value
        )

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


class DelongiPrimadonnaUtilitySensor(DelongiPrimadonnaStatisticsSensor):
    """
    Sensor that tracks usage over a period (daily/weekly).
    Disabled by default.
    """

    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        device: DelongiPrimadonna,
        hass: HomeAssistant,
        sensor_type: str,
        param_id: int,
        name: str,
        native_unit_of_measurement: str = None,
        period: str = "daily",
        icon: str = 'mdi:counter'
    ) -> None:
        """Initialize the utility sensor."""
        super().__init__(
            device, hass, sensor_type, param_id, name,
            native_unit_of_measurement, icon
        )
        self._period = period
        self._start_value = None
        self._last_period_id = None

    @property
    def _current_period_id(self) -> str:
        """Get the current period identifier."""
        from datetime import datetime
        now = datetime.now()
        if self._period == "daily":
            return now.strftime("%Y-%m-%d")
        return now.strftime("%Y-%W")

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._start_value = last_state.attributes.get("start_value")
            self._last_period_id = last_state.attributes.get("last_period_id")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "start_value": self._start_value,
            "last_period_id": self._last_period_id,
            "period": self._period
        }

    @property
    def native_value(self):
        """Return the current period usage."""
        total_value = super().native_value
        if total_value is None:
            return None

        current_period = self._current_period_id

        # Initialize or reset if period changed or start value is missing
        if self._last_period_id != current_period or self._start_value is None:
            self._start_value = total_value
            self._last_period_id = current_period
            # Trigger state save to persist start_value and last_period_id
            self.async_write_ha_state()
            return 0

        return round(max(0, total_value - self._start_value), 2)
