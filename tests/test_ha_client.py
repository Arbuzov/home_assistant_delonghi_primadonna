from unittest.mock import patch, AsyncMock
from datetime import datetime
import pytest
from custom_components.delonghi_primadonna.delonghi_ha_client import DelonghiPrimaDonnaHAClient


@pytest.mark.asyncio
async def test_set_time_calls_device_client(hass):
    """Test that set_time method calls device client."""
    config = {"mac": "aa:bb:cc:dd:ee:ff", "name": "Test", "model": "model"}
    
    with patch('custom_components.delonghi_primadonna.delonghi_ha_client.DelonghiPrimaDonnaClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        client = DelonghiPrimaDonnaHAClient(config, hass)
        
        # Call set_time
        test_time = datetime(2023, 1, 1, 12, 0)
        await client.set_time(test_time)
        
        # Verify it was called
        mock_client.set_time.assert_called_once_with(test_time)


def test_client_properties(hass):
    """Test that client exposes correct properties."""
    config = {"mac": "aa:bb:cc:dd:ee:ff", "name": "Test", "model": "model"}
    
    with patch('custom_components.delonghi_primadonna.delonghi_ha_client.DelonghiPrimaDonnaClient') as mock_client_class:
        # Configure the mock to return the expected values
        mock_client_instance = mock_client_class.return_value
        mock_client_instance.mac = "aa:bb:cc:dd:ee:ff"
        mock_client_instance.name = "Test"
        mock_client_instance.model = "model"
        mock_client_instance.add_status_handler = AsyncMock()
        mock_client_instance.add_profile_handler = AsyncMock()
        mock_client_instance.add_statistics_handler = AsyncMock()
        
        client = DelonghiPrimaDonnaHAClient(config, hass)
        
        assert client.mac == "aa:bb:cc:dd:ee:ff"
        assert client.name == "Test" 
        assert client.model == "model"
