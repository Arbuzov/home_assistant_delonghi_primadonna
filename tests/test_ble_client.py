import copy
from unittest.mock import patch

from custom_components.delonghi_primadonna.ble_client import (
    AVAILABLE_PROFILES,
    DelongiPrimadonna,
)
from custom_components.delonghi_primadonna.models import MachineModel


def test_init_uses_n_profiles(hass):
    """DelongiPrimadonna should read n_profiles from machine model."""
    config = {"mac": "aa:bb:cc:dd:ee:ff", "name": "Test", "model": "model"}
    machine = MachineModel(n_profiles=2)
    profiles_backup = copy.deepcopy(AVAILABLE_PROFILES)
    try:
        with patch(
            "custom_components.delonghi_primadonna.ble_client.get_machine_model",
            return_value=machine,
        ):
            client = DelongiPrimadonna(config, hass)
        assert client._n_profiles == 2
        assert client.profiles == ["Profile 1", "Profile 2"]
        assert list(AVAILABLE_PROFILES.keys()) == [1, 2]
    finally:
        AVAILABLE_PROFILES.clear()
        AVAILABLE_PROFILES.update(profiles_backup)

