from __future__ import annotations

from dataclasses import dataclass, field

try:
    from enum import IntEnum
except ImportError:  # pragma: no cover - fallback for older Home Assistant
    from homeassistant.backports.enum import IntEnum

from typing import Any


# Custom recipe constants (IDs vary by machine group: 230-239)
CUSTOM_RECIPE_NAME = "Custom"
CUSTOM_ID_RANGE = [230, 231, 232, 233, 234, 235, 236, 237, 238, 239]

# Mapping from recipe ID to display name
RECIPE_ID_TO_NAME = {
    1: "Espresso Coffee",
    2: "Regular Coffee", 
    3: "Long Coffee",
    4: "2X Espresso Coffee",
    5: "Doppio+",
    6: "Americano",
    7: "Cappuccino",
    8: "Latte Macchiato",
    9: "Caffé Latte",
    10: "Flat White",
    11: "Espresso Macchiato",
    12: "Hot Milk",
    13: "Cappuccino Doppio+",
    14: "Cold Milk",
    15: "Cappuccino Reverse",
    16: "Hot Water",
    17: "Steam",
    18: "Ciocco",
    19: "Ristretto",  # Also "Custom 01"
    20: "Espresso lungo",  # Also "Custom 02"
    21: "Caffè freddo",  # Also "Custom 03"
    22: "Tea",  # Also "Custom 04"
    23: "Coffee pot",  # Also "Custom 05"
    24: "Cortado",  # Also "Custom 06"
    25: "Long Black",
    26: "Travel Mug",
    27: "Brew Over Ice",
    50: "Iced Americano",
    51: "Iced Cappuccino",
    52: "Iced Latte Macchiato",
    53: "Iced Cappuccino Mix",
    54: "Iced Flat White",
    55: "Iced Cold Milk",
    56: "Iced Caffelatte",
    80: "Mug Americano",
    81: "Mug Cappuccino",
    82: "Mug Latte Macchiato",
    83: "Mug Caffelatte",
    84: "Mug Cappuccino Mix",
    85: "Mug Flat White",
    86: "Mug Hot Milk",
    100: "Mug Iced Brew Over ice",
    101: "Mug Iced Americano",
    102: "Mug Iced Cappuccino",
    103: "Mug Iced Latte Macchiato",
    104: "Mug Iced Caffelatte",
    105: "Mug Iced Cappuccino Mix",
    106: "Mug Iced Flat White",
    107: "Mug Iced Cold Milk",
    200: "Espresso BS 1",
}


class BeverageName(IntEnum):
    """Known beverage names from bundled machine data with their fixed recipe IDs.
    
    Each enum value corresponds directly to the recipe ID from MachinesModels.json.
    Based on analysis showing that name->id mappings are consistent across all models.
    Custom recipes are excluded as they have variable IDs (230-239) per machine group.
    """

    ESPRESSO_COFFEE = 1
    REGULAR_COFFEE = 2
    LONG_COFFEE = 3
    _2X_ESPRESSO_COFFEE = 4
    DOPPIOPLUS = 5
    AMERICANO = 6
    CAPPUCCINO = 7
    LATTE_MACCHIATO = 8
    CAFFE_LATTE = 9
    FLAT_WHITE = 10
    ESPRESSO_MACCHIATO = 11
    HOT_MILK = 12
    CAPPUCCINO_DOPPIOPLUS = 13
    COLD_MILK = 14
    CAPPUCCINO_REVERSE = 15
    HOT_WATER = 16
    STEAM = 17
    CIOCCO = 18
    RISTRETTO = 19  # Also used for CUSTOM_01
    ESPRESSO_LUNGO = 20  # Also used for CUSTOM_02
    CAFFE_FREDDO = 21  # Also used for CUSTOM_03
    TEA = 22  # Also used for CUSTOM_04
    COFFEE_POT = 23  # Also used for CUSTOM_05
    CORTADO = 24  # Also used for CUSTOM_06
    LONG_BLACK = 25
    TRAVEL_MUG = 26
    BREW_OVER_ICE = 27
    ICED_AMERICANO = 50
    ICED_CAPPUCCINO = 51
    ICED_LATTE_MACCHIATO = 52
    ICED_CAPPUCCINO_MIX = 53
    ICED_FLAT_WHITE = 54
    ICED_COLD_MILK = 55
    ICED_CAFFELATTE = 56
    MUG_AMERICANO = 80
    MUG_CAPPUCCINO = 81
    MUG_LATTE_MACCHIATO = 82
    MUG_CAFFELATTE = 83
    MUG_CAPPUCCINO_MIX = 84
    MUG_FLAT_WHITE = 85
    MUG_HOT_MILK = 86
    MUG_ICED_BREW_OVER_ICE = 100
    MUG_ICED_AMERICANO = 101
    MUG_ICED_CAPPUCCINO = 102
    MUG_ICED_LATTE_MACCHIATO = 103
    MUG_ICED_CAFFELATTE = 104
    MUG_ICED_CAPPUCCINO_MIX = 105
    MUG_ICED_FLAT_WHITE = 106
    MUG_ICED_COLD_MILK = 107
    ESPRESSO_BS_1 = 200

    @property
    def recipe_id(self) -> int:
        """Get the recipe ID for this beverage (same as enum value)."""
        return self.value

    @property
    def display_name(self) -> str:
        """Get the display name for this beverage."""
        return RECIPE_ID_TO_NAME.get(self.value, f"Unknown Recipe {self.value}")

    @classmethod
    def from_name(cls, name: str) -> "BeverageName | None":
        """Get BeverageName by recipe display name."""
        for recipe_id, display_name in RECIPE_ID_TO_NAME.items():
            if display_name == name:
                try:
                    return cls(recipe_id)
                except ValueError:
                    continue
        return None

    @classmethod
    def from_id(cls, recipe_id: int | str) -> "BeverageName | None":
        """Get BeverageName by recipe ID."""
        try:
            recipe_id_int = int(recipe_id)
            return cls(recipe_id_int)
        except (ValueError, TypeError):
            return None

    @classmethod
    def is_custom_recipe(cls, name: str | None = None, recipe_id: int | str | None = None) -> bool:
        """Check if a recipe is a custom recipe by name or ID."""
        if name:
            return name == CUSTOM_RECIPE_NAME
        if recipe_id is not None:
            try:
                recipe_id_int = int(recipe_id)
                return recipe_id_int in CUSTOM_ID_RANGE
            except (ValueError, TypeError):
                return False
        return False

    def __str__(self) -> str:
        """Return the display name when converted to string."""
        return self.display_name


@dataclass(slots=True)
class Recipe:
    """Recipe description for a machine."""

    taste: int | None = None
    name: BeverageName | str | None = None
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
