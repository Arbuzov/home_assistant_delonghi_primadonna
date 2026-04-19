from binascii import unhexlify

def parse_statistics(data: bytes):
    """Accurate mirror of the logic in device.py"""
    statistics = {}
    if len(data) < 8:
        return statistics

    # First parameter: Implicit ID from bytes 4 and 5
    pid = (data[4] << 8) | data[5]
    val = int.from_bytes(data[6:10], byteorder='big')
    statistics[pid] = val
    
    # Subsequent parameters (if any) are in the format [ID 2B] + [Value 4B]
    current_offset = 10
    # Check if there is at least one more [ID 2B] + [Val 4B] block before CRC (last 2 bytes)
    while current_offset + 6 <= len(data) - 2:
        pid = (data[current_offset] << 8) | data[current_offset+1]
        val = int.from_bytes(data[current_offset+2:current_offset+6], byteorder='big')
        statistics[pid] = val
        current_offset += 6
        
    return statistics

def test_parsing():
    # Packet from user's logs
    # d0 41 a2 0f 00 64 00 13 a8 9e 00 65 00 00 00 0a 00 69 00 00 00 0f 00 6a 00 23 65 e8 00 6c 00 00 00 00 00 6d 00 00 00 00 00 6f 00 00 00 12 00 74 00 00 02 84 02 84 00 00 00 00 0b b8 00 00 39 7e 54 d1
    
    log_packet = unhexlify("d041a20f00640013a89e00650000000a00690000000f006a002365e8006c00000000006d00000000006f000000120074000002840284000000000bb80000397e54d1")
    
    stats = parse_statistics(log_packet)
    
    print(f"ID 100 (Implicit): {stats.get(100)}")
    print(f"ID 101 (Explicit): {stats.get(101)}")
    print(f"ID 105 (Explicit): {stats.get(105)}")
    print(f"ID 106 (Explicit/Water): {stats.get(106)}")
    print(f"ID 111 (Explicit/Milk Cleaning): {stats.get(111)}") 
    print(f"ID 116 (Explicit/Water?): {stats.get(116)}") 
    
    # Let's mock a packet with Tea and Choco as well to verify the loop
    # d0 41 a2 0f 00 64 00 13 a8 9e (ID 100)
    # 0b c9 (ID 3017/Cold Milk) 00 00 00 0a (Val 10)
    # 0b cd (ID 3021/Choco) 00 00 00 05 (Val 5)
    # 0b d1 (ID 3025/Tea) 00 00 00 0f (Val 15)
    # 39 7e (CRC)
    
    mock_packet = unhexlify("d00fa20f0bc90000000a0bcd000000050bd10000000f397e")
    mock_stats = parse_statistics(mock_packet)
    
    print(f"Mock ID 3017: {mock_stats.get(3017)}")
    print(f"Mock ID 3021: {mock_stats.get(3021)}")
    print(f"Mock ID 3025: {mock_stats.get(3025)}")
    
    assert mock_stats[3017] == 10
    assert mock_stats[3021] == 5
    assert mock_stats[3025] == 15
    
    # Also verify the original packet assertions
    assert stats[100] == 1288350
    assert stats[101] == 10
    assert stats[105] == 15
    assert stats[106] == 2319848
    assert stats[111] == 18
    assert stats[116] == 644
    
    print("\n[SUCCESS] Standalone parsing logic verified for all IDs.")

if __name__ == "__main__":
    test_parsing()
