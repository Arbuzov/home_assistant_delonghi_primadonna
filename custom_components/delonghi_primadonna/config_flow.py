"""Config flow for the Delonghi Primadonna integration."""

from __future__ import annotations

import json
import logging

from binascii import hexlify
from importlib import resources
from typing import Any

import voluptuous
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_MAC, CONF_MODEL, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (SelectOptionDict, SelectSelector,
                                            SelectSelectorConfig,
                                            SelectSelectorMode)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _load_model_options() -> list[SelectOptionDict]:
    """Load machine models from bundled JSON."""
    options: list[SelectOptionDict] = []
    try:
        with resources.files(__package__).joinpath("MachinesModels.json").open(
            "r", encoding="utf-8"
        ) as file:
            data = json.load(file)
    except Exception as err:  # pragma: no cover
        _LOGGER.error("Failed to load machine models: %s", err)
        return options

    for machine in filter(
        lambda m: m.get("connectionType") == "BT", data.get("machines", [])
    ):
        name = machine.get("name")
        code = machine.get("product_code")
        if name and code:
            options.append(SelectOptionDict(value=code, label=name))
    return options


MODEL_OPTIONS = _load_model_options()

STEP_USER_DATA_SCHEMA = voluptuous.Schema(
    {
        voluptuous.Required(
            CONF_NAME, description={"suggested_value": "My Precious"}
        ): str,
        voluptuous.Required(CONF_MAC): str,
        voluptuous.Required(CONF_MODEL): SelectSelector(
            SelectSelectorConfig(
                options=MODEL_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
                sort=True,
            )
        ),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for delonghi."""

    VERSION = 1

    def __init__(self):
        self._schema = STEP_USER_DATA_SCHEMA

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.info(
            "Discovered Delonghi device: %s %s %s",
            discovery_info.address,
            discovery_info.name,
            hexlify(bytearray(discovery_info.raw), " "
        )
        _LOGGER.warning("Dump all discovery info: %s", discovery_info)

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._schema = voluptuous.Schema(
            {
                voluptuous.Required(
                    CONF_NAME,
                    description={"suggested_value": discovery_info.name},
                ): str,
                voluptuous.Required(
                    CONF_MAC,
                    description={"suggested_value": discovery_info.address},
                ): str,
                voluptuous.Required(CONF_MODEL): SelectSelector(
                    SelectSelectorConfig(
                        options=MODEL_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                        sort=True,
                    )
                ),
            }
        )

        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=self._schema,
            )
        else:
            await self.async_set_unique_id(user_input[CONF_MAC])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )
