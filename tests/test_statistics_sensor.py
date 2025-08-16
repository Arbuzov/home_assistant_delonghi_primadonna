import pytest
from unittest.mock import MagicMock

from custom_components.delonghi_primadonna.sensor import DelongiPrimadonnaStatisticsSensor
from custom_components.delonghi_primadonna.const import DOMAIN


@pytest.mark.asyncio
async def test_statistics_sensor_attributes_update(hass):
    device = MagicMock()
    device.mac = "aa:bb:cc:dd:ee:ff"
    device.name = "Test"
    device.model = "model"
    device.statistics = [10, 20, 30]

    sensor = DelongiPrimadonnaStatisticsSensor(device, hass)
    sensor.entity_id = "sensor.statistics_debug"
    await sensor.async_added_to_hass()

    assert sensor.native_value == 3
    assert sensor.extra_state_attributes == {
        "stat_1": 10,
        "stat_2": 20,
        "stat_3": 30,
    }

    hass.bus.async_fire(f"{DOMAIN}_statistics", {"statistics": [1, 2]})
    await hass.async_block_till_done()

    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == {
        "stat_1": 1,
        "stat_2": 2,
    }
