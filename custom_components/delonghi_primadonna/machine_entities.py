from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


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
