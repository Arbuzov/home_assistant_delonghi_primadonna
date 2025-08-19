"""Data structures and utilities for machine models and beverages.

All enumerations, dataclasses, mappings, and lightweight loader utilities used
across the integration are collected here to keep other modules tidy and make
the available capabilities explicit in one place.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum, IntFlag
from importlib import resources
from typing import Any
from functools import lru_cache

try:  # Python 3.11+
    from enum import StrEnum  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - fallback for older Home Assistant
    try:
        from homeassistant.backports.enum import StrEnum  # type: ignore
    except Exception:  # final fallback if HA backport is unavailable
        class StrEnum(str, Enum):
            pass

from .const import (AMERICANO_OFF, AMERICANO_ON, COFFE_OFF, COFFE_ON,
                    COFFEE_GROUNDS_CONTAINER_CLEAN,
                    COFFEE_GROUNDS_CONTAINER_DETACHED,
                    COFFEE_GROUNDS_CONTAINER_FULL, DEBUG, DEVICE_READY,
                    DEVICE_TURNOFF, DOPPIO_OFF, DOPPIO_ON, ESPRESSO2_OFF,
                    ESPRESSO2_ON, ESPRESSO_OFF, ESPRESSO_ON, HOTWATER_OFF,
                    HOTWATER_ON, LONG_OFF, LONG_ON, START_COFFEE, STEAM_OFF,
                    STEAM_ON, WATER_SHORTAGE, WATER_TANK_DETACHED)

# BeverageName enum is dynamically generated from bundled machine data to
# avoid manual upkeep of a long static list.


def _enum_name(value: str) -> str:
    """Convert an arbitrary beverage string to a valid enum name."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = value.replace("+", "PLUS").replace("&", "AND")
    value = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_")
    if value and value[0].isdigit():
        value = f"_{value}"
    return value.upper()


def _load_beverage_names() -> list[str]:
    """Return sorted beverage names from the bundled machine models file."""
    with resources.files(__package__).joinpath("MachinesModels.json").open(
        "r", encoding="utf-8"
    ) as file:
        data = json.load(file)
    names: set[str] = set()
    for machine in data.get("machines", []):
        for recipe in machine.get("recipes", []):
            name = recipe.get("name")
            if name:
                names.add(name)
    return sorted(names)


BeverageName = StrEnum(
    "BeverageName", {_enum_name(name): name for name in _load_beverage_names()}
)


@dataclass(slots=True)
class Recipe:
    """Recipe description for a machine."""

    taste: int | None = None
    name: str | None = None
    coffee_qty: int | None = None
    milk_qty: int | None = None
    min_milk: int | None = None
    max_milk: int | None = None
    ingredients: list[str] = field(default_factory=list)
    min_coffee: int | None = None
    id: str | None = None
    max_coffee: int | None = None
    use_for_custom_recipes: bool | None = None


@dataclass(slots=True)
class MachineModel:
    """Machine model description."""

    profile_names_customizable: bool | None = None
    character_set: str | None = None
    profile_icons_set: str | None = None
    auto_start_settings: bool | None = None
    global_temperature: bool | None = None
    filter_settings: bool | None = None
    product_code: str | None = None
    type: str | None = None
    auto_off_settings: bool | None = None
    connection_type: str | None = None
    buzzer_settings: bool | None = None
    multibeverage: bool | None = None
    creation_recipes: bool | None = None
    image_name: str | None = None
    water_hardness_settings: bool | None = None
    default: bool | None = None
    cup_warmer_settings: bool | None = None
    image2_url: str | None = None
    protocol_version: int | None = None
    id: int | None = None
    app_model_id: str | None = None
    recipes: list[Recipe] = field(default_factory=list)
    image_url: str | None = None
    cup_light_settings: bool | None = None
    time_settings: bool | None = None
    profile_icons_customizable: bool | None = None
    n_grinders: int | None = None
    pin_settings: bool | None = None
    n_custom_recipes: int | None = None
    energy_saving_settings: bool | None = None
    protocol_minor_version: int | None = None
    name: str | None = None
    customizable_profiles: bool | None = None
    n_standard_recipes: int | None = None
    n_profiles: int | None = None
    international_sku: bool | None = None


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


# -----------------------------
# Models loader/utilities
# -----------------------------

def _to_snake_case(key: str) -> str:
    """Convert camelCase/PascalCase keys to snake_case expected by dataclasses."""
    if key.lower() == "internationalsku":
        return "international_sku"
    return re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()


@lru_cache
def get_machine_models() -> "MachineModels":
    """Return machine data parsed into dataclasses.

    Uses a tiny cache to avoid re-reading JSON on repeated calls.
    """
    with resources.files(__package__).joinpath("MachinesModels.json").open(
        "r", encoding="utf-8"
    ) as file:
        data = json.load(file)

    models = MachineModels(
        result=data.get("result", {}),
        name=data.get("name"),
        version=data.get("version"),
    )

    for machine in data.get("machines", []):
        recipes: list[Recipe] = []
        for r in machine.get("recipes", []):
            r_snake = {_to_snake_case(k): v for k, v in r.items()}
            name = r_snake.get("name")
            r_snake["name"] = (
                BeverageName(name)
                if name in BeverageName._value2member_map_
                else None
            )
            recipes.append(Recipe(**r_snake))
        machine_snake = {
            _to_snake_case(k): v for k, v in machine.items() if k != "recipes"
        }
        models.machines.append(MachineModel(**{**machine_snake, "recipes": recipes}))
    return models


def get_machine_model(product_code: str) -> "MachineModel | None":
    """Return machine model by product code."""
    if product_code is None:
        return None
    return next(
        (
            model
            for model in get_machine_models().machines
            if model.product_code == product_code
        ),
        None,
    )


def get_machine_models_by_connection(connection_type: str = "BT") -> list["MachineModel"]:
    """Return machine models of the given connection type."""
    return [
        model
        for model in get_machine_models().machines
        if model.connection_type == connection_type
    ]


def guess_machine_model(name: str) -> "MachineModel | None":
    """Return machine model for a Bluetooth name."""
    if not name:
        return None

    base = name[1:] if name.startswith("D") else name
    if len(base) <= 2:
        return None

    suffix = base[:-2]

    for model in get_machine_models().machines:
        product_code = model.product_code
        if product_code and str(product_code).endswith(suffix):
            return model
    return None

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
    "get_machine_models",
    "get_machine_model",
    "get_machine_models_by_connection",
    "guess_machine_model",
]
