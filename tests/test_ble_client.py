from unittest.mock import AsyncMock, patch

from datetime import datetime
import pytest

from custom_components.delonghi_primadonna.ble_client import DelongiPrimadonna
from custom_components.delonghi_primadonna.const import BYTES_TIME_COMMAND
from custom_components.delonghi_primadonna.models import MachineModel


def test_init_uses_n_profiles(hass, monkeypatch):
    """DelongiPrimadonna should read n_profiles from machine model."""
    config = {"mac": "aa:bb:cc:dd:ee:ff", "name": "Test", "model": "model"}
    machine = MachineModel(n_profiles=2)
    patched_profiles = {1: "Profile 1", 2: "Profile 2", 3: "Profile 3"}
    monkeypatch.setattr(
        "custom_components.delonghi_primadonna.ble_client.AVAILABLE_PROFILES",
        patched_profiles,
    )
    with patch(
        "custom_components.delonghi_primadonna.ble_client.get_machine_model",
        return_value=machine,
    ):
        client = DelongiPrimadonna(config, hass)
    assert client._n_profiles == 2
    assert client.profiles == ["Profile 1", "Profile 2"]
    assert list(patched_profiles.keys()) == [1, 2]


@pytest.mark.parametrize("machine", [None, MachineModel(n_profiles=None)])
def test_init_fallbacks_to_default_profiles(hass, monkeypatch, machine):
    """Client should fall back to default profiles when model missing."""
    config = {"mac": "aa:bb:cc:dd:ee:ff", "name": "Test", "model": "model"}
    patched_profiles = {1: "Profile 1", 2: "Profile 2", 3: "Profile 3"}
    monkeypatch.setattr(
        "custom_components.delonghi_primadonna.ble_client.AVAILABLE_PROFILES",
        patched_profiles,
    )
    with patch(
        "custom_components.delonghi_primadonna.ble_client.get_machine_model",
        return_value=machine,
    ):
        client = DelongiPrimadonna(config, hass)
    assert client._n_profiles == 3
    assert client.profiles == ["Profile 1", "Profile 2", "Profile 3"]
    assert list(patched_profiles.keys()) == [1, 2, 3]


@pytest.mark.asyncio
async def test_set_time_builds_packet(hass):
    dt = datetime(2024, 1, 2, 3, 4)
    config = {"mac": "aa:bb:cc:dd:ee:ff", "name": "Test", "model": "model"}
    client = DelongiPrimadonna(config, hass)
    client.send_command = AsyncMock()

    await client.set_time(dt)

    expected = BYTES_TIME_COMMAND.copy()
    expected[4] = 3
    expected[5] = 4
    client.send_command.assert_awaited_once_with(expected)

