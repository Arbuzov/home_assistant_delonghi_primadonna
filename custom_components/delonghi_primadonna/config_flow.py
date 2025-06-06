"""Config flow for the Delonghi Primadonna integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = voluptuous.Schema(
    {
        voluptuous.Required(
            CONF_NAME, description={'suggested_value': 'My Precious'}
        ): str,
        voluptuous.Required(CONF_MAC): str,
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
            'Discovered Delonghi device: %s %s',
            discovery_info.address,
            discovery_info.name,
        )

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._schema = voluptuous.Schema(
            {
                voluptuous.Required(
                    CONF_NAME, description={
                        'suggested_value': discovery_info.name
                    }
                ): str,
                voluptuous.Required(
                    CONF_MAC, description={
                        'suggested_value': discovery_info.address
                    }
                ): str,
            }
        )

        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        if user_input is None:
            return self.async_show_form(
                step_id='user',
                data_schema=self._schema
            )
        else:
            await self.async_set_unique_id(user_input[CONF_MAC])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input
            )
