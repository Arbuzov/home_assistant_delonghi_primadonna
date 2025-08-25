"""Tests for statistics sensor handling."""

from unittest.mock import MagicMock

import pytest

from custom_components.delonghi_primadonna.const import DOMAIN
from custom_components.delonghi_primadonna.sensor import (
    DelongiPrimadonnaStatisticsSensor,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "initial_stats",
    [
        [],
        [42],
        [10, 20, 30],
        list(range(1000)),
    ],
)
async def test_statistics_sensor_attributes_update(hass, initial_stats):
    """Ensure the sensor exposes table attributes for various inputs."""
    device = MagicMock()
    device.mac = "aa:bb:cc:dd:ee:ff"
    device.name = "Test"
    device.model = "model"
    device.statistics = initial_stats

    sensor = DelongiPrimadonnaStatisticsSensor(device, hass)
    sensor.entity_id = "sensor.statistics_debug"
    await sensor.async_added_to_hass()

    assert sensor.native_value == len(initial_stats)
    expected = {"statistics": initial_stats}
    expected.update(
        {f"stat_{idx + 1}": val for idx, val in enumerate(initial_stats)}
    )
    assert sensor.extra_state_attributes == expected

    hass.bus.async_fire(f"{DOMAIN}_statistics", {"statistics": [1, 2]})
    await hass.async_block_till_done()

    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == {
        "statistics": [1, 2],
        "stat_1": 1,
        "stat_2": 2,
    }

    # Update with an empty list to ensure stats reset
    hass.bus.async_fire(f"{DOMAIN}_statistics", {"statistics": []})
    await hass.async_block_till_done()

    assert sensor.native_value == 0
    assert sensor.extra_state_attributes == {"statistics": []}

@pytest.mark.asyncio
async def test_statistics_sensor_invalid_statistics(hass):
    """Ensure invalid statistics updates are ignored."""
    device = MagicMock()
    device.mac = "aa:bb:cc:dd:ee:ff"
    device.name = "Test"
    device.model = "model"
    device.statistics = [1, 2]

    sensor = DelongiPrimadonnaStatisticsSensor(device, hass)
    sensor.entity_id = "sensor.statistics_debug"
    await sensor.async_added_to_hass()

    expected = {
        "statistics": [1, 2],
        "stat_1": 1,
        "stat_2": 2,
    }

    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == expected

    hass.bus.async_fire(f"{DOMAIN}_statistics", {"statistics": None})
    await hass.async_block_till_done()
    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == expected

    hass.bus.async_fire(
        f"{DOMAIN}_statistics", {"statistics": ["a", 2.5, {}, []]}
    )
    await hass.async_block_till_done()
    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == expected

    hass.bus.async_fire(f"{DOMAIN}_statistics", {"not_statistics": [1, 2, 3]})
    await hass.async_block_till_done()
    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == expected

    hass.bus.async_fire(
        f"{DOMAIN}_statistics", {"statistics": "not_a_list"}
    )
    await hass.async_block_till_done()
    assert sensor.native_value == 2
    assert sensor.extra_state_attributes == expected

