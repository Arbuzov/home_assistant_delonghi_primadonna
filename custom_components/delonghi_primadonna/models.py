"""Data structures describing beverage commands, statuses and notifications.

All enumerations, dataclasses and mappings used across the integration are
collected here to keep the other modules tidy and make the available
capabilities explicit in one place.
"""

from dataclasses import dataclass
from enum import IntFlag

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - fallback for older Home Assistant
    from homeassistant.backports.enum import StrEnum

from .const import (AMERICANO_OFF, AMERICANO_ON, COFFE_OFF, COFFE_ON,
                    COFFEE_GROUNDS_CONTAINER_CLEAN,
                    COFFEE_GROUNDS_CONTAINER_DETACHED,
                    COFFEE_GROUNDS_CONTAINER_FULL, DEBUG, DEVICE_READY,
                    DEVICE_TURNOFF, DOPPIO_OFF, DOPPIO_ON, ESPRESSO2_OFF,
                    ESPRESSO2_ON, ESPRESSO_OFF, ESPRESSO_ON, HOTWATER_OFF,
                    HOTWATER_ON, LONG_OFF, LONG_ON, START_COFFEE, STEAM_OFF,
                    STEAM_ON, WATER_SHORTAGE, WATER_TANK_DETACHED)


class BeverageEntityFeature(IntFlag):
    """Supported features of the beverage entity."""

    MAKE_BEVERAGE = 1
    SET_TEMPERATURE = 2
    SET_INTENCE = 4


class AvailableBeverage(StrEnum):
    """Coffee machine available beverages."""

    NONE = "none"
    STEAM = "steam"
    LONG = "long"
    COFFEE = "coffee"
    DOPIO = "dopio"
    HOTWATER = "hot_water"
    ESPRESSO = "espresso"
    AMERICANO = "americano"
    ESPRESSO2 = "espresso2"


NOZZLE_STATE = {
    -1: "unknown",
    0: "detached",
    1: "steam",
    2: "milk_frother",
    4: "milk_frother_cleaning",
}

SERVICE_STATE = {0: "OK", 4: "DESCALING"}

DEVICE_STATUS = {
    3: "COOKING",
    4: "NOZZLE_DETACHED",
    5: "OK",
    13: "COFFEE_GROUNDS_CONTAINER_DETACHED",
    21: "WATER_TANK_DETACHED",
}


class NotificationType(StrEnum):
    """Coffee machine notification types."""

    STATUS = "status"
    PROCESS = "process"


@dataclass(slots=True)
class BeverageCommand:
    """Byte sequences used to start and stop a beverage."""

    on: list[int]
    off: list[int]


@dataclass(slots=True)
class BeverageNotify:
    """Description of a notification produced by the machine."""

    kind: str
    description: str


@dataclass(slots=True)
class DeviceSwitches:
    """Current states of machine switches and toggles."""

    sounds: bool = False
    energy_save: bool = False
    cup_light: bool = False
    filter: bool = False
    is_on: bool = False


BEVERAGE_COMMANDS = {
    AvailableBeverage.NONE: BeverageCommand(DEBUG, DEBUG),
    AvailableBeverage.STEAM: BeverageCommand(STEAM_ON, STEAM_OFF),
    AvailableBeverage.LONG: BeverageCommand(LONG_ON, LONG_OFF),
    AvailableBeverage.COFFEE: BeverageCommand(COFFE_ON, COFFE_OFF),
    AvailableBeverage.DOPIO: BeverageCommand(DOPPIO_ON, DOPPIO_OFF),
    AvailableBeverage.HOTWATER: BeverageCommand(HOTWATER_ON, HOTWATER_OFF),
    AvailableBeverage.ESPRESSO: BeverageCommand(ESPRESSO_ON, ESPRESSO_OFF),
    AvailableBeverage.AMERICANO: BeverageCommand(AMERICANO_ON, AMERICANO_OFF),
    AvailableBeverage.ESPRESSO2: BeverageCommand(ESPRESSO2_ON, ESPRESSO2_OFF),
}

DEVICE_NOTIFICATION = {
    str(bytearray(DEVICE_READY)): BeverageNotify(
        NotificationType.STATUS,
        "DeviceOK",
    ),
    str(bytearray(DEVICE_TURNOFF)): BeverageNotify(
        NotificationType.STATUS,
        "DeviceOFF",
    ),
    str(bytearray(WATER_TANK_DETACHED)): BeverageNotify(
        NotificationType.STATUS,
        "NoWaterTank",
    ),
    str(bytearray(WATER_SHORTAGE)): BeverageNotify(
        NotificationType.STATUS,
        "NoWater",
    ),
    str(bytearray(COFFEE_GROUNDS_CONTAINER_DETACHED)): BeverageNotify(
        NotificationType.STATUS,
        "NoGroundsContainer",
    ),
    str(bytearray(COFFEE_GROUNDS_CONTAINER_FULL)): BeverageNotify(
        NotificationType.STATUS,
        "GroundsContainerFull",
    ),
    str(bytearray(COFFEE_GROUNDS_CONTAINER_CLEAN)): BeverageNotify(
        NotificationType.STATUS,
        "GroundsContainerFull",
    ),
    str(bytearray(START_COFFEE)): BeverageNotify(
        NotificationType.STATUS,
        "START_COFFEE",
    ),
}

__all__ = [
    "BeverageEntityFeature",
    "AvailableBeverage",
    "NotificationType",
    "BeverageCommand",
    "BeverageNotify",
    "DeviceSwitches",
    "NOZZLE_STATE",
    "SERVICE_STATE",
    "DEVICE_STATUS",
    "BEVERAGE_COMMANDS",
    "DEVICE_NOTIFICATION",
]
