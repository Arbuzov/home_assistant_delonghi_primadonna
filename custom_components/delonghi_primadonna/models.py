"""Data structures describing machine models, beverage commands and statuses.

All enumerations, dataclasses and mappings used across the integration are
collected here to keep the other modules tidy and make the available
capabilities explicit in one place.
"""

from dataclasses import dataclass, field
from enum import IntFlag
from typing import Any

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


class BeverageName(StrEnum):
    """Known beverage names from bundled machine data."""

    _2X_ESPRESSO_COFFEE = "2X Espresso Coffee"
    AMERICANO = "Americano"
    BREW_OVER_ICE = "Brew Over Ice"
    CAFFE_FREDDO = "Caffè freddo"
    CAFFE_LATTE = "Caffé Latte"
    CAPPUCCINO = "Cappuccino"
    CAPPUCCINO_DOPPIOPLUS = "Cappuccino Doppio+"
    CAPPUCCINO_REVERSE = "Cappuccino Reverse"
    CIOCCO = "Ciocco"
    COFFEE_POT = "Coffee pot"
    COLD_MILK = "Cold Milk"
    CORTADO = "Cortado"
    CUSTOM = "Custom"
    CUSTOM_01 = "Custom 01"
    CUSTOM_02 = "Custom 02"
    CUSTOM_03 = "Custom 03"
    CUSTOM_04 = "Custom 04"
    CUSTOM_05 = "Custom 05"
    CUSTOM_06 = "Custom 06"
    DOPPIOPLUS = "Doppio+"
    ESPRESSO_BS_1 = "Espresso BS 1"
    ESPRESSO_COFFEE = "Espresso Coffee"
    ESPRESSO_MACCHIATO = "Espresso Macchiato"
    ESPRESSO_LUNGO = "Espresso lungo"
    FLAT_WHITE = "Flat White"
    HOT_MILK = "Hot Milk"
    HOT_WATER = "Hot Water"
    ICED_AMERICANO = "Iced Americano"
    ICED_CAFFELATTE = "Iced Caffelatte"
    ICED_CAPPUCCINO = "Iced Cappuccino"
    ICED_CAPPUCCINO_MIX = "Iced Cappuccino Mix"
    ICED_COLD_MILK = "Iced Cold Milk"
    ICED_FLAT_WHITE = "Iced Flat White"
    ICED_LATTE_MACCHIATO = "Iced Latte Macchiato"
    LATTE_MACCHIATO = "Latte Macchiato"
    LONG_BLACK = "Long Black"
    LONG_COFFEE = "Long Coffee"
    MUG_AMERICANO = "Mug Americano"
    MUG_CAFFELATTE = "Mug Caffelatte"
    MUG_CAPPUCCINO = "Mug Cappuccino"
    MUG_CAPPUCCINO_MIX = "Mug Cappuccino Mix"
    MUG_FLAT_WHITE = "Mug Flat White"
    MUG_HOT_MILK = "Mug Hot Milk"
    MUG_ICED_AMERICANO = "Mug Iced Americano"
    MUG_ICED_BREW_OVER_ICE = "Mug Iced Brew Over ice"
    MUG_ICED_CAFFELATTE = "Mug Iced Caffelatte"
    MUG_ICED_CAPPUCCINO = "Mug Iced Cappuccino"
    MUG_ICED_CAPPUCCINO_MIX = "Mug Iced Cappuccino Mix"
    MUG_ICED_COLD_MILK = "Mug Iced Cold Milk"
    MUG_ICED_FLAT_WHITE = "Mug Iced Flat White"
    MUG_ICED_LATTE_MACCHIATO = "Mug Iced Latte Macchiato"
    MUG_LATTE_MACCHIATO = "Mug Latte Macchiato"
    REGULAR_COFFEE = "Regular Coffee"
    RISTRETTO = "Ristretto"
    STEAM = "Steam"
    TEA = "Tea"
    TRAVEL_MUG = "Travel Mug"


@dataclass(slots=True)
class Recipe:
    """Recipe description for a machine."""

    taste: int | None = None
    name: BeverageName | None = None
    coffee_qty: int | None = None
    milk_qty: int | None = None
    min_milk: int | None = None
    max_milk: int | None = None
    ingredients: list[str] = field(default_factory=list)
    min_coffee: int | None = None
    id: str | None = None
    max_coffee: int | None = None
    useForCustomRecipes: bool | None = None


@dataclass(slots=True)
class MachineModel:
    """Machine model description."""

    profile_names_customizable: bool | None = None
    characterSet: str | None = None
    profile_icons_set: str | None = None
    auto_start_settings: bool | None = None
    globalTemperature: bool | None = None
    filter_settings: bool | None = None
    product_code: str | None = None
    type: str | None = None
    auto_off_settings: bool | None = None
    connectionType: str | None = None
    buzzer_settings: bool | None = None
    multibeverage: bool | None = None
    creationRecipes: bool | None = None
    image_name: str | None = None
    water_hardness_settings: bool | None = None
    default: bool | None = None
    cup_warmer_settings: bool | None = None
    image2_url: str | None = None
    protocolVersion: int | None = None
    id: int | None = None
    appModelId: str | None = None
    recipes: list[Recipe] = field(default_factory=list)
    image_url: str | None = None
    cup_light_settings: bool | None = None
    time_settings: bool | None = None
    profile_icons_customizable: bool | None = None
    nGrinders: int | None = None
    pin_settings: bool | None = None
    nCustomRecipes: int | None = None
    energy_saving_settings: bool | None = None
    protocol_minor_version: int | None = None
    name: str | None = None
    customizableProfiles: bool | None = None
    nStandardRecipes: int | None = None
    nProfiles: int | None = None
    internationalsku: bool | None = None


@dataclass(slots=True)
class MachineModels:
    """Container for all machine models."""

    result: dict[str, Any] = field(default_factory=dict)
    name: str | None = None
    machines: list[MachineModel] = field(default_factory=list)
    version: str | None = None


class BeverageEntityFeature(IntFlag):
    """Supported features of the beverage entity."""

    MAKE_BEVERAGE = 1
    SET_TEMPERATURE = 2
    SET_INTENSITY = 4


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
        "GroundsContainerClean",
    ),
    str(bytearray(START_COFFEE)): BeverageNotify(
        NotificationType.STATUS,
        "START_COFFEE",
    ),
}

__all__ = [
    "BeverageName",
    "BeverageEntityFeature",
    "AvailableBeverage",
    "NotificationType",
    "Recipe",
    "MachineModel",
    "MachineModels",
    "BeverageCommand",
    "BeverageNotify",
    "DeviceSwitches",
    "NOZZLE_STATE",
    "SERVICE_STATE",
    "DEVICE_STATUS",
    "BEVERAGE_COMMANDS",
    "DEVICE_NOTIFICATION",
]
