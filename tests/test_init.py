import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant

from custom_components.delonghi_primadonna import async_setup_entry, async_unload_entry
from custom_components.delonghi_primadonna.const import DOMAIN


@pytest.mark.asyncio
async def test_async_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """Test integration setup and unload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        data={"mac": "aa:bb:cc:dd:ee:ff", "model": "model", "name": "Test"},
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.delonghi_primadonna.DelongiPrimadonna",
            autospec=True,
        ) as mock_device,
        patch.object(
            hass.config_entries, "async_forward_entry_setups", AsyncMock(return_value=True)
        ),
    ):
        mock_instance = mock_device.return_value
        mock_instance.get_device_name = AsyncMock(return_value=None)
        mock_instance.disconnect = AsyncMock(return_value=None)

        assert await async_setup_entry(hass, entry)
        assert entry.unique_id in hass.data[DOMAIN]

        assert await async_unload_entry(hass, entry)
        assert entry.unique_id not in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_config_flow_user_form() -> None:
    """Test that the initial user form is shown."""
    from custom_components.delonghi_primadonna.config_flow import ConfigFlow

    flow = ConfigFlow()
    result = await flow.async_step_user()
    assert result["type"] == "form"
    assert result["step_id"] == "user"
