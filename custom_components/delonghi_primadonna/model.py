"""Utilities for machine model data."""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from importlib import resources
from typing import Any

from homeassistant.helpers.selector import SelectOptionDict

_LOGGER = logging.getLogger(__name__)


@lru_cache
def _load_machines() -> list[dict[str, Any]]:
    """Load machine models from bundled JSON."""
    try:
        with resources.files(__package__).joinpath("MachinesModels.json").open(
            "r", encoding="utf-8"
        ) as file:
            data = json.load(file)
        return data.get("machines", [])
    except Exception as err:  # pragma: no cover
        _LOGGER.error("Failed to load machine models: %s", err)
        return []


def get_model(product_code: str) -> dict[str, Any] | None:
    """Return attributes for a model by product code."""
    for machine in _load_machines():
        if machine.get("product_code") == product_code:
            return machine
    return None


def get_model_options(connection_type: str = "BT") -> list[SelectOptionDict]:
    """Return selector options for models of the given connection type."""
    options: list[SelectOptionDict] = []
    for machine in filter(
        lambda m: m.get("connectionType") == connection_type, _load_machines()
    ):
        name = machine.get("name")
        code = machine.get("product_code")
        if name and code:
            options.append(SelectOptionDict(value=code, label=name))
    return options
