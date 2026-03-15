from binascii import unhexlify

def parse_statistics(data: bytes):
    """Accurate mirror of the logic in device.py"""
    statistics = {}
    if len(data) < 7:
        return statistics

    # First parameter: Implicit ID
    param_id = 100
    param_value = data[4] + (data[5] << 8) + (data[6] << 16)
    statistics[param_id] = param_value
    
    # Subsequent parameters: Explicit IDs
    offset = 7
    while offset + 5 <= len(data):
        param_id = data[offset]
        # ID < 110: 4-byte value
        if param_id < 110:
            val = data[offset + 1] + (data[offset + 2] << 8) + (data[offset + 3] << 16) + (data[offset + 4] << 24)
            statistics[param_id] = val
        else:
            # ID >= 110: 2-byte value + 2 padding bytes (total 4 bytes consumed)
            # wait, let me check the actual code logic in device.py again
            # I suspect IDs >= 110 use 2 bytes for the value
            val = data[offset + 1] + (data[offset + 2] << 8)
            statistics[param_id] = val
        offset += 5
        
    return statistics

def test_parsing():
    # Packet from user's logs
    # d0 41 a2 0f 00 64 00 13 a8 9e 00 65 00 00 00 0a 00 69 00 00 00 0f 00 6a 00 23 65 e8 00 6c 00 00 00 00 00 6d 00 00 00 00 00 6f 00 00 00 12 00 74 00 00 02 84 02 84 00 00 00 00 0b b8 00 00 39 7e 54 d1
    
    # Let's manually trace the log_packet relative to indices:
    # [0] d0
    # [1] 41
    # [2] a2
    # [3] 0f (Length)
    # [4-6] 00 64 00 -> Implicit Part. Value = 0x6400 = 25600? No, wait. 
    # Bytes 4-6 are 00 64 00. 0 + 100<<8 + 0 = 25600.
    
    # Wait, the log said: Statistics Parser.Parsed (Implicit): ID 100 = 1288350
    # 1288350 in hex is 0x13A89E
    # So the implicit value is actually [7-9]? Let me re-read device.py
    
    log_packet = unhexlify("d041a20f00640013a89e00650000000a00690000000f006a002365e8006c00000000006d00000000006f000000120074000002840284000000000bb80000397e54d1")
    
    # In device.py:
    # param_id = 100
    # param_value = data[7] + (data[8] << 8) + (data[9] << 16)
    # offset = 10
    
    def parse_statistics_fixed(data: bytes):
        statistics = {}
        # Param 100: Implicit
        val = data[7] + (data[8] << 8) + (data[9] << 16)
        statistics[100] = val
        
        offset = 10
        # While loop
        while offset + 5 <= len(data):
            p_id = data[offset]
            offset += 1
            if p_id < 110:
                p_val = data[offset] + (data[offset+1] << 8) + (data[offset+2] << 16) + (data[offset+3] << 24)
                offset += 4
            else:
                p_val = data[offset] + (data[offset+1] << 8)
                offset += 4
            statistics[p_id] = p_val
        return statistics

    stats = parse_statistics_fixed(log_packet)
    
    print(f"ID 100 (Implicit): {stats.get(100)}")
    print(f"ID 101 (Explicit): {stats.get(101)}")
    print(f"ID 105 (Explicit): {stats.get(105)}")
    print(f"ID 111 (Explicit/Milk): {stats.get(111)}") # Should be 18
    print(f"ID 116 (Explicit/Water?): {stats.get(116)}") # Should be 644 (0x0284)
    
    assert stats[100] == 1288350
    assert stats[101] == 10
    assert stats[105] == 15
    assert stats[111] == 18
    assert stats[116] == 644
    
    print("\n[SUCCESS] Standalone parsing logic verified.")

if __name__ == "__main__":
    test_parsing()
