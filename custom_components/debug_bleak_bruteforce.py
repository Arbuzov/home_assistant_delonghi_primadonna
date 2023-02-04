import asyncio
import binascii
import uuid
from binascii import hexlify

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

MAC = "00:A0:50:82:75:CA"
NAME_CHARACTERISTIC = '00002A00-0000-1000-8000-00805F9B34FB'
GENERAL_SERVICE = '00001801-0000-1000-8000-00805f9b34fb'
BYTES_POWER = [0x0d, 0x07, 0x84, 0x0f, 0x02, 0x01, 0x55, 0x12]
CONTROLL_CHARACTERISTIC = '00035b03-58e6-07dd-021a-08123a000301'


def sign_request(message):
    """Request signer"""
    deviser = 0x1d0f
    for item in message[:len(message) - 2]:
        i3 = (((deviser << 8) | (deviser >> 8)) &
              0x0000ffff) ^ (item & 0xffff)
        i4 = i3 ^ ((i3 & 0xff) >> 4)
        i5 = i4 ^ ((i4 << 12) & 0x0000ffff)
        deviser = i5 ^ (((i5 & 0xff) << 5) & 0x0000ffff)
    signature = list((deviser & 0x0000ffff).to_bytes(2, byteorder='big'))
    message[len(message) - 2] = signature[0]
    message[len(message) - 1] = signature[1]
    return message


def handle_data(sender, value):
    print('Received data: %s from %s', hexlify(value, ' '), sender)


async def main(ble_address: str):
    device = await BleakScanner.find_device_by_address(ble_address, timeout=20.0)
    async with BleakClient(ble_address) as client:
        await client.start_notify(
            uuid.UUID(CONTROLL_CHARACTERISTIC),
            handle_data
        )
        services = await client.get_services()
        print("Services:")
        for service in services:
            print(service)
        value = bytes(await client.read_gatt_char(uuid.UUID(NAME_CHARACTERISTIC))).decode('utf-8')
        print(value)

        print(BYTES_POWER)
        for x in range(0, 255):
            for y in range(0, 255):
                for z in range(0, 255):
                    new_bytes = BYTES_POWER
                    new_bytes[1] = x
                    new_bytes[4] = y
                    new_bytes[5] = z
                    new_bytes = sign_request(new_bytes)
                    print(new_bytes)
                    await client.write_gatt_char(CONTROLL_CHARACTERISTIC,
                                                 bytearray(new_bytes))
                    await asyncio.sleep(4)

asyncio.run(main(MAC))
