"""Regressions for the dispensing binary sensor."""

import asyncio
import os
import sys

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
        )
    )
)

from delonghi_primadonna.binary_sensor import \
    DelongiPrimadonnaDispensingSensor  # noqa: E402
from delonghi_primadonna.device import DelongiPrimadonna  # noqa: E402
from delonghi_primadonna.device import parse_monitor_data  # noqa: E402

CONFIG = {
    "mac": "00:11:22:33:44:55",
    "model": "TEST",
    "name": "TEST",
}


def monitor_v2(status: int, sub_status: int, percentage: int) -> bytes:
    """Build a 0x75 monitor frame with the fields under test."""
    data = bytearray(16)
    data[0] = 0xD0
    data[1] = 0x12
    data[2] = 0x75
    data[8] = 0x00
    data[9] = status
    data[10] = sub_status
    data[11] = percentage
    return bytes(data)


def make_device():
    return DelongiPrimadonna(CONFIG, None)


def apply(device, status, sub_status, percentage):
    packet = monitor_v2(status, sub_status, percentage)
    parsed = parse_monitor_data(packet)
    device._handle_monitor_data(parsed, 0x75, packet)
    return parsed


async def test_percentage_is_parsed_from_byte_11():
    parsed = parse_monitor_data(monitor_v2(7, 4, 63))
    assert parsed.percentage == 63


async def test_ready_with_progress_counts_as_dispensing():
    """State 7 is both idle and dispensing; sub_status separates them."""
    device = make_device()

    apply(device, 7, 4, 63)
    assert device.is_dispensing is True
    assert device.dispensing_percentage == 63

    apply(device, 7, 0, 0)
    assert device.is_dispensing is False


async def test_milk_and_hot_water_states_count_as_dispensing():
    device = make_device()

    apply(device, 10, 0, 20)
    assert device.is_dispensing is True
    apply(device, 11, 0, 40)
    assert device.is_dispensing is True


async def test_steam_counts_maintenance_does_not():
    """Steam (5) is a dispense; descaling, milk cleaning, filter are not.

    A measured 96 s steam dispense reported state 5 throughout and never
    state 7, so without 5 the sensor stayed off for the whole dispense.
    """
    device = make_device()

    apply(device, 5, 2, 30)
    assert device.is_dispensing is True
    for maintenance in (4, 12, 14):
        apply(device, maintenance, 1, 50)
        assert device.is_dispensing is False, maintenance


async def test_percentage_is_cleared_when_idle():
    device = make_device()

    apply(device, 7, 4, 63)
    apply(device, 7, 0, 63)

    assert device.dispensing_percentage == 0


async def test_sensor_reflects_the_device():
    device = make_device()
    sensor = DelongiPrimadonnaDispensingSensor(device, None)

    apply(device, 7, 4, 55)
    assert sensor.is_on is True
    assert sensor.extra_state_attributes == {'percentage': 55}

    apply(device, 7, 0, 0)
    assert sensor.is_on is False


async def run_tests():
    await test_percentage_is_parsed_from_byte_11()
    await test_ready_with_progress_counts_as_dispensing()
    await test_milk_and_hot_water_states_count_as_dispensing()
    await test_steam_counts_maintenance_does_not()
    await test_percentage_is_cleared_when_idle()
    await test_sensor_reflects_the_device()
    print("[SUCCESS] Dispensing sensor verified.")


if __name__ == "__main__":
    asyncio.run(run_tests())
