from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import AvailableBeverage, DelonghiDeviceEntity, DelongiPrimadonna


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    delongh_device: DelongiPrimadonna = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([
        DelongiPrimadonnaPowerButton(delongh_device),
        DelongiPrimadonnaLongButton(delongh_device),
        DelongiPrimadonnaCoffeeButton(delongh_device),
        DelongiPrimadonnaDopioButton(delongh_device),
        DelongiPrimadonnaSteamButton(delongh_device),
        DelongiPrimadonnaHotWaterButton(delongh_device),
        DelongiPrimadonnaEspresso2Button(delongh_device),
        DelongiPrimadonnaAmericanoButton(delongh_device),
        DelongiPrimadonnaEspressoButton(delongh_device),
        DelongiPrimadonnaCancelButton(delongh_device),
        DelongiPrimadonnaDebugButton(delongh_device)
    ])
    return True


class DelongiPrimadonnaPowerButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Turn on'

    async def async_press(self):
        await self.device.power_on()


class DelongiPrimadonnaLongButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Prepare long'

    async def async_press(self):
        await self.device.beverage_start(AvailableBeverage.LONG)


class DelongiPrimadonnaCoffeeButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Prepare Coffee'

    async def async_press(self):
        await self.device.beverage_start(AvailableBeverage.COFFEE)


class DelongiPrimadonnaDopioButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Prepare Doppio+'

    async def async_press(self):
        await self.device.beverage_start(AvailableBeverage.DOPIO)


class DelongiPrimadonnaSteamButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Prepare Steam'

    async def async_press(self):
        await self.device.beverage_start(AvailableBeverage.STEAM)


class DelongiPrimadonnaHotWaterButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Prepare Hot Water'

    async def async_press(self):
        await self.device.beverage_start(AvailableBeverage.HOTWATER)


class DelongiPrimadonnaEspresso2Button(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Prepare x2 Espresso'

    async def async_press(self):
        await self.device.beverage_start(AvailableBeverage.ESPRESSO2)


class DelongiPrimadonnaAmericanoButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Prepare Americano'

    async def async_press(self):
        await self.device.beverage_start(AvailableBeverage.AMERICANO)


class DelongiPrimadonnaEspressoButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Prepare Espresso'

    async def async_press(self):
        await self.device.beverage_start(AvailableBeverage.ESPRESSO)


class DelongiPrimadonnaCancelButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Cancel cooking'

    async def async_press(self):
        await self.device.beverage_cancel()


class DelongiPrimadonnaDebugButton(DelonghiDeviceEntity, ButtonEntity):

    _attr_name = 'Debug'

    async def async_press(self):
        await self.device.debug()
