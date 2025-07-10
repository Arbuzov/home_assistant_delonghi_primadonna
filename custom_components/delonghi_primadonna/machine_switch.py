from __future__ import annotations

from enum import Enum
from typing import List


class MachineSwitch(Enum):
    """Known machine switches."""

    WATER_SPOUT = "water_spout"
    MOTOR_UP = "motor_up"
    MOTOR_DOWN = "motor_down"
    COFFEE_WASTE_CONTAINER = "coffee_waste_container"
    WATER_TANK_ABSENT = "water_tank_absent"
    KNOB = "knob"
    WATER_LEVEL_LOW = "water_level_low"
    COFFEE_JUG = "coffee_jug"
    IFD_CARAFFE = "ifd_caraffe"
    CIOCCO_TANK = "ciocco_tank"
    CLEAN_KNOB = "clean_knob"
    DOOR_OPENED = "door_opened"
    PREGROUND_DOOR_OPENED = "preground_door_opened"
    COFFEE_BEANS_EMPTY = "coffee_beans_empty"
    UNKNOWN_SWITCH = "unknown_switch"
    IGNORE_SWITCH = "ignore_switch"


_SWITCH_BIT_MAP: dict[int, MachineSwitch] = {
    0: MachineSwitch.WATER_SPOUT,
    1: MachineSwitch.IGNORE_SWITCH,
    # Some devices report an additional bit when the grounds container is full
    # or needs cleaning. Treat that bit the same as the standard
    # ``COFFEE_WASTE_CONTAINER`` so the ``Switches`` sensor shows the state
    # correctly.
    2: MachineSwitch.COFFEE_WASTE_CONTAINER,
    3: MachineSwitch.COFFEE_WASTE_CONTAINER,
    4: MachineSwitch.WATER_TANK_ABSENT,
    5: MachineSwitch.KNOB,
    6: MachineSwitch.IGNORE_SWITCH,
    7: MachineSwitch.IGNORE_SWITCH,
    8: MachineSwitch.IFD_CARAFFE,
    9: MachineSwitch.CIOCCO_TANK,
    10: MachineSwitch.CLEAN_KNOB,
    11: MachineSwitch.IGNORE_SWITCH,
    12: MachineSwitch.IGNORE_SWITCH,
    13: MachineSwitch.DOOR_OPENED,
    14: MachineSwitch.PREGROUND_DOOR_OPENED,
}


def switch_from_bit(index: int) -> MachineSwitch:
    """Return machine switch for a bit index."""
    return _SWITCH_BIT_MAP.get(index, MachineSwitch.UNKNOWN_SWITCH)


def parse_switches(data: bytes) -> List[MachineSwitch]:
    """Parse switch states from a monitor mode response."""
    if len(data) < 8:
        return []

    service = data[7]
    if service == 0x08:
        return [MachineSwitch.COFFEE_BEANS_EMPTY]

    mask = data[5] | (data[6] << 8)
    result: List[MachineSwitch] = []
    for bit in range(16):
        if mask & (1 << bit):
            sw = switch_from_bit(bit)
            if sw not in (
                MachineSwitch.IGNORE_SWITCH,
                MachineSwitch.WATER_SPOUT,
                MachineSwitch.IFD_CARAFFE,
                MachineSwitch.CIOCCO_TANK,
                MachineSwitch.UNKNOWN_SWITCH,
            ) and sw not in result:
                result.append(sw)
    return result


__all__ = ["MachineSwitch", "parse_switches", "switch_from_bit"]
