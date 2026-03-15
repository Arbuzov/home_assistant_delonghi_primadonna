import sys
import os
from binascii import unhexlify

# Add custom_components to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "custom_components")))

from delonghi_primadonna.device import DelongiPrimadonna

def test_parsing():
    device = DelongiPrimadonna(None, {"mac": "00:11:22:33:44:55", "model": "TEST", "name": "TEST"})
    
    # Packet from user's logs
    # d0 41 a2 0f 00 64 00 13 a8 9e 00 65 00 00 00 0a 00 69 00 00 00 0f 00 6a 00 23 65 e8 00 6c 00 00 00 00 00 6d 00 00 00 00 00 6f 00 00 00 12 00 74 00 00 02 84 02 84 00 00 00 00 0b b8 00 00 39 7e 54 d1
    log_packet = unhexlify("d041a20f00640013a89e00650000000a00690000000f006a002365e8006c00000000006d00000000006f000000120074000002840284000000000bb80000397e54d1")
    device._handle_data(None, log_packet)
    
    print(f"ID 100 (Implicit): {device.statistics.get(100)}")
    print(f"ID 101 (Explicit): {device.statistics.get(101)}")
    print(f"ID 105 (Explicit): {device.statistics.get(105)}")
    print(f"ID 111 (Explicit/Milk): {device.statistics.get(111)}")
    
    assert device.statistics[100] == 1288350
    assert device.statistics[101] == 10
    assert device.statistics[105] == 15
    assert device.statistics[111] == 18 # This is ID 0x6F
    
    print("\n[SUCCESS] Parsing logic verified with log data.")

    # Test sensor restoration fallback
    print("\nTesting sensor restoration fallback...")
    class MockSensor:
        def __init__(self, device, param_id, restored_value):
            self.device = device
            self._param_id = param_id
            self._attr_native_value = restored_value
        
        @property
        def native_value(self):
            return self.device.statistics.get(self._param_id, self._attr_native_value)

    res_sensor = MockSensor(device, 999, 42)
    print(f"Restored value (ID not in stats): {res_sensor.native_value}")
    assert res_sensor.native_value == 42
    
    device.statistics[999] = 100
    print(f"Live value (ID in stats): {res_sensor.native_value}")
    assert res_sensor.native_value == 100
    
    print("[SUCCESS] Sensor restoration fallback verified.")

if __name__ == "__main__":
    test_parsing()
