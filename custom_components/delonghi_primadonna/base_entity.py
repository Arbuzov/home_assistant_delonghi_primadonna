from .const import DOMAIN
from .device import DelongiPrimadonna
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

class DelonghiDeviceEntity:
    """Entity class for the Delonghi devices"""

    _attr_has_entity_name = True

    def __init__(self, delongh_device, hass: HomeAssistant):
        """Init entity with the device"""
        self._attr_unique_id = (
            f'{delongh_device.mac}_'
            f'{self.__class__.__name__}'
        )
        self.device: DelongiPrimadonna = delongh_device
        self.hass = hass

    @property
    def device_info(self):
        """Shared device info information"""
        return {
            'identifiers': {(DOMAIN, self.device.mac)},
            'connections': {(dr.CONNECTION_NETWORK_MAC, self.device.mac)},
            'name': self.device.name,
            'manufacturer': 'Delonghi',
            'model': self.device.model,
        }

