"""Utilities for machine model data."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from importlib import resources

from .machine_entities import BeverageName, MachineModel, MachineModels, Recipe

_LOGGER = logging.getLogger(__name__)


@lru_cache
def get_machine_models() -> MachineModels:
    """Return machine data parsed into dataclasses."""
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
            name = r.get("name")
            r["name"] = (
                BeverageName(name)
                if name in BeverageName._value2member_map_
                else None
            )
            recipes.append(Recipe(**r))
        models.machines.append(MachineModel(**{**machine, "recipes": recipes}))
    return models


def get_machine_model(product_code: str) -> MachineModel | None:
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


def get_machine_models_by_connection(
    connection_type: str = "BT",
) -> list[MachineModel]:
    """Return machine models of the given connection type."""
    return [
        model
        for model in get_machine_models().machines
        if model.connectionType == connection_type
    ]


def guess_machine_model(name: str) -> MachineModel | None:
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
