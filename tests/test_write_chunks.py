import os
import sys
from binascii import unhexlify

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
        )
    )
)

from delonghi_primadonna.device import DelongiPrimadonna  # noqa: E402

CONFIG = {
    "mac": "00:11:22:33:44:55",
    "model": "TEST",
    "name": "TEST",
}

# Coffee Link starting an Espresso Macchiato on a Maestosa (EPAM960.75.GLM),
# from an iOS Bluetooth log: 25 bytes, sent as a 20-byte write then a 5-byte
# write. The machine ignored the same frame sent as a single write.
MACCHIATO_START = unhexlify(
    "0d1883f00b010002"
    "01004f0203040009"
    "00520b011c020612"
    "a0"
)
APP_WRITES = [MACCHIATO_START[:20], MACCHIATO_START[20:]]


class RecordingClient:
    is_connected = True

    def __init__(self):
        self.writes = []

    async def write_gatt_char(
        self,
        _characteristic,
        _message,
    ):
        self.writes.append(bytes(_message))


async def fake_connect():
    return None


def make_device(client):
    device = DelongiPrimadonna(CONFIG, None)
    device._client = client
    device._connect = fake_connect
    return device


async def test_long_frame_is_written_in_20_byte_chunks(monkeypatch):
    monkeypatch.setattr("asyncio.wait_for", fake_wait_for)
    client = RecordingClient()
    device = make_device(client)

    # The CRC bytes are recomputed by send_command
    await device.send_command(list(MACCHIATO_START[:-2]) + [0, 0], retries=1)

    assert client.writes == APP_WRITES


async def test_short_frame_is_one_write(monkeypatch):
    monkeypatch.setattr("asyncio.wait_for", fake_wait_for)
    client = RecordingClient()
    device = make_device(client)
    ristretto = [0x0D, 0x13, 0x83, 0xF0, 0x01, 0x01, 0x00, 0x00,
                 0x01, 0x00, 0x32, 0x02, 0x05, 0x04, 0x01, 0x08,
                 0x00, 0x06, 0x00, 0x00]

    await device.send_command(ristretto, retries=1)

    assert len(client.writes) == 1
    assert len(client.writes[0]) == 20


async def fake_wait_for(awaitable, timeout):
    """No machine to answer, so skip the 10 s reply wait."""
    awaitable.close()
    raise TimeoutError
