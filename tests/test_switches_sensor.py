"""Regressions for the switches sensor (#285)."""

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

from delonghi_primadonna.device import DelongiPrimadonna  # noqa: E402
from delonghi_primadonna.machine_switch import MachineSwitch  # noqa: E402
from delonghi_primadonna.sensor import \
    DelongiPrimadonnaSwitchesSensor  # noqa: E402

CONFIG = {
    "mac": "00:11:22:33:44:55",
    "model": "TEST",
    "name": "TEST",
}


def make_sensor(*switches):
    device = DelongiPrimadonna(CONFIG, None)
    device.active_switches = list(switches)
    return DelongiPrimadonnaSwitchesSensor(device, None)


def test_no_switch_is_none():
    sensor = make_sensor()
    assert sensor.native_value == "none"
    assert sensor.extra_state_attributes == {"active_switches": []}


def test_single_switch():
    sensor = make_sensor(MachineSwitch.MOTOR_DOWN)
    assert sensor.native_value == "motor_down"


def test_several_switches_report_one_valid_option():
    """Two active switches used to be joined into an invalid state."""
    sensor = make_sensor(
        MachineSwitch.MOTOR_DOWN, MachineSwitch.WATER_LEVEL_LOW
    )
    assert sensor.native_value in sensor.options
    assert sensor.native_value == "water_level_low"
    assert sensor.extra_state_attributes == {
        "active_switches": ["motor_down", "water_level_low"],
    }


def test_alert_wins_over_other_alert_by_priority():
    sensor = make_sensor(
        MachineSwitch.MOTOR_DOWN,
        MachineSwitch.COFFEE_WASTE_CONTAINER,
        MachineSwitch.WATER_TANK_ABSENT,
    )
    assert sensor.native_value == "water_tank_absent"


def test_without_alert_first_active_switch_wins():
    sensor = make_sensor(MachineSwitch.MOTOR_UP, MachineSwitch.KNOB)
    assert sensor.native_value == "motor_up"


def test_every_combination_is_a_valid_option():
    candidates = [
        s for s in MachineSwitch
        if s not in (
            MachineSwitch.IGNORE_SWITCH, MachineSwitch.UNKNOWN_SWITCH
        )
    ]
    for first in candidates:
        for second in candidates:
            sensor = make_sensor(first, second)
            assert sensor.native_value in sensor.options
