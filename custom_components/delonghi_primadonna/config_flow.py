"""Config flow for the Delonghi Primadonna integration."""

from __future__ import annotations

import logging
from binascii import hexlify
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
from .model import get_machine_models_by_connection, guess_machine_model

_LOGGER = logging.getLogger(__name__)


MODEL_OPTIONS = [
    SelectOptionDict(value=model.product_code, label=model.name)
    for model in get_machine_models_by_connection()
    if model.product_code and model.name
]

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
        raw_data = discovery_info.raw
        if raw_data is None:
            try:
                from bluetooth_data_tools.utils import newest_manufacturer_data

                raw_data = newest_manufacturer_data(
                    discovery_info.manufacturer_data or {}
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Failed to get raw manufacturer data: %s", err)

        raw_hex = hexlify(bytearray(raw_data), " ") if raw_data else "none"

        _LOGGER.info(
            "Discovered Delonghi device: %s %s %s",
            discovery_info.address,
            discovery_info.name,
            raw_hex,
        )
        _LOGGER.debug("Dump all discovery info: %s", discovery_info)

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        default_machine = guess_machine_model(discovery_info.name)
        model_schema = voluptuous.Required(CONF_MODEL)
        suggested_name = discovery_info.name
        if default_machine:
            model_schema = voluptuous.Required(
                CONF_MODEL, default=default_machine.product_code
            )
            suggested_name = default_machine.name or suggested_name

        self._schema = voluptuous.Schema(
            {
                voluptuous.Required(
                    CONF_NAME,
                    description={"suggested_value": suggested_name},
                ): str,
                voluptuous.Required(
                    CONF_MAC,
                    description={"suggested_value": discovery_info.address},
                ): str,
                model_schema: SelectSelector(
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


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for existing entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the Delonghi configuration."""

        if user_input is None:
            data = self.config_entry.data
            return self.async_show_form(
                step_id="init",
                data_schema=voluptuous.Schema(
                    {
                        voluptuous.Required(
                            CONF_NAME, default=data.get(CONF_NAME)
                        ): str,
                        voluptuous.Required(
                            CONF_MAC, default=data.get(CONF_MAC)
                        ): str,
                        voluptuous.Required(
                            CONF_MODEL, default=data.get(CONF_MODEL)
                        ): SelectSelector(
                            SelectSelectorConfig(
                                options=MODEL_OPTIONS,
                                mode=SelectSelectorMode.DROPDOWN,
                                sort=True,
                            )
                        ),
                    }
                ),
            )

        await self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=user_input,
        )
        self.hass.async_create_task(
            self.hass.config_entries.async_reload(self.config_entry.entry_id)
        )
        return self.async_create_entry(title="", data={})


async def async_get_options_flow(
    config_entry: config_entries.ConfigEntry,
) -> OptionsFlowHandler:
    """Return the options flow handler."""

    return OptionsFlowHandler(config_entry)
