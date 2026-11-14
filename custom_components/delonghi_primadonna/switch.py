"""Switch entities for Delonghi Primadonna."""

import datetime
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .base_entity import DelonghiDeviceEntity
from .const import DOMAIN, STANDBY_VERIFIED_PRODUCT_CODES
from .device import DelongiPrimadonna
from .model import get_machine_model


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
):
    """Register switch entities for a config entry."""

    delongh_device: DelongiPrimadonna = hass.data[DOMAIN][entry.unique_id]
    model = get_machine_model(delongh_device.product_code)

    switches = [
        DelongiPrimadonnaNotificationSwitch(delongh_device, hass),
        DelongiPrimadonnaPowerSaveSwitch(delongh_device, hass),
        DelongiPrimadonnaSoundsSwitch(delongh_device, hass),
    ]

    if delongh_device.product_code in STANDBY_VERIFIED_PRODUCT_CODES:
        switches.append(
            DelongiPrimadonnaPowerSwitch(delongh_device, hass),
        )

    if model and model.cup_light_settings:
        switches.insert(
            0,
            DelongiPrimadonnaCupLightSwitch(delongh_device, hass),
        )

    if model and model.time_settings:
        switches.insert(
            0,
            DelongiPrimadonnaTimeSyncSwitch(delongh_device, hass),
        )

    async_add_entities(switches)
    return True


class SettingsBackedSwitch:
    """Shared refresh for the switches carried by the settings parameter.

    All of them are answered by one read of parameter 0x3f, so the request is
    issued once here and throttled in the device rather than per entity.
    """

    async def async_update(self) -> None:
        """Refresh the settings parameter from the device."""
        if self.device.connected:
            await self.device.update_switches()


class DelongiPrimadonnaCupLightSwitch(
    SettingsBackedSwitch, DelonghiDeviceEntity, ToggleEntity, RestoreEntity
):
    """This switch enable/disable the cup light"""

    _attr_icon = 'mdi:lightbulb'
    _attr_translation_key = 'cup_light'

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self.device.switches.cup_light = last_state.state == 'on'

    @property
    def is_on(self) -> bool:
        """Return the state read back from the device."""
        return self.device.switches.cup_light

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.CONFIG

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        self.device.switches.cup_light = True
        self.hass.async_create_task(self.device.cup_light_on())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        self.device.switches.cup_light = False
        self.hass.async_create_task(self.device.cup_light_off())


class DelongiPrimadonnaNotificationSwitch(
    DelonghiDeviceEntity, ToggleEntity, RestoreEntity
):
    """This switch enable HA side bar notification
       on device status change used for debug purposes
    """

    _attr_is_on = False
    _attr_icon = 'mdi:magnify-expand'
    _attr_translation_key = 'debug_notification'

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self.device.notify = last_state.state == 'on'

    @property
    def is_on(self, **kwargs: Any) -> None:
        """Checks is the notification ON."""
        return self.device.notify

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.DIAGNOSTIC

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the notification on."""
        self.device.notify = True

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the notification off."""
        self.device.notify = False


class DelongiPrimadonnaPowerSaveSwitch(
    SettingsBackedSwitch, DelonghiDeviceEntity, ToggleEntity, RestoreEntity
):

    _attr_icon = 'mdi:lightning-bolt'
    _attr_translation_key = 'energy_save_mode'

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self.device.switches.energy_save = last_state.state == 'on'

    @property
    def is_on(self) -> bool:
        """Return the state read back from the device."""
        return self.device.switches.energy_save

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity"""
        return EntityCategory.CONFIG

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the energy save on"""
        self.device.switches.energy_save = True
        self.hass.async_create_task(self.device.energy_save_on())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the energy save off"""
        self.device.switches.energy_save = False
        self.hass.async_create_task(self.device.energy_save_off())


class DelongiPrimadonnaSoundsSwitch(
    SettingsBackedSwitch, DelonghiDeviceEntity, ToggleEntity, RestoreEntity
):

    _attr_icon = 'mdi:volume-high'
    _attr_translation_key = 'sounds'

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self.device.switches.sounds = last_state.state == 'on'

    @property
    def is_on(self) -> bool:
        """Return the state read back from the device."""
        return self.device.switches.sounds

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.CONFIG

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the sounds on."""
        self.device.switches.sounds = True
        self.hass.async_create_task(self.device.sound_alarm_on())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the sounds off."""
        self.device.switches.sounds = False
        self.hass.async_create_task(self.device.sound_alarm_off())


class DelongiPrimadonnaTimeSyncSwitch(
        DelonghiDeviceEntity, ToggleEntity, RestoreEntity
):
    """Keep the machine clock in step with Home Assistant.

    While on, the clock is set right away if the machine is awake, or
    once it wakes up, and then re-synced once a day.
    """

    _attr_icon = 'mdi:clock-time-eight-outline'
    _attr_translation_key = 'time_sync'

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self.device.sync_time = last_state.state == 'on'

    @property
    def is_on(self) -> bool:
        """Return whether time synchronization is enabled."""
        return self.device.sync_time

    @property
    def entity_category(self, **kwargs: Any) -> None:
        """Return the category of the entity."""
        return EntityCategory.CONFIG

    # Set when a sync is due but the machine is in standby.
    _sync_pending = False

    async def async_update(self) -> None:
        """Re-sync the clock once a day while enabled.

        A machine in standby does not answer the clock command (it drew
        no reply for the full timeout), so a due sync waits until the
        machine is awake and goes out on the first poll after that.
        """
        if not self.device.sync_time:
            return
        now = time.monotonic()
        if (
            not self._sync_pending
            and now - self.device.last_time_sync < 24 * 3600
        ):
            return
        if not self.device.switches.is_on:
            self._sync_pending = True
            return
        self._sync_pending = False
        self.device.last_time_sync = now
        self.hass.async_create_task(self._sync_clock())

    async def _sync_clock(self) -> None:
        """Set the clock; if nothing came back, try again in an hour."""
        if not await self.device.set_time(datetime.datetime.now()):
            # Due again by the daily rule one hour after this attempt, so
            # a machine that never answers is not asked on every poll.
            self.device.last_time_sync -= 23 * 3600

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable time sync and set the clock now, or once awake."""
        self.device.sync_time = True
        self._sync_pending = True
        await self.async_update()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable time synchronization."""
        self.device.sync_time = False


class DelongiPrimadonnaPowerSwitch(DelonghiDeviceEntity, ToggleEntity):
    """Turn the machine on, or put it into standby.

    Only offered on the models listed in STANDBY_VERIFIED_PRODUCT_CODES.
    The state follows the machine status from the monitor packets, so it
    also reflects use of the physical power button.
    """

    _attr_icon = 'mdi:power'
    _attr_translation_key = 'power'

    @property
    def is_on(self) -> bool:
        """Return True while the machine is not in standby."""
        return self.device.switches.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the machine on."""
        self.hass.async_create_task(self.device.power_on())

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Put the machine into standby."""
        self.hass.async_create_task(self.device.power_off())
