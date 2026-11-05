import asyncio
import os
import sys
from binascii import unhexlify

import pytest
from bleak.exc import BleakError

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


class FailingClient(RecordingClient):
    """Fails the given write (1-based) by raising ``error``."""

    def __init__(self, fail_on, error):
        super().__init__()
        self.fail_on = fail_on
        self.error = error
        self.disconnects = 0

    async def write_gatt_char(
        self,
        _characteristic,
        _message,
    ):
        if len(self.writes) + 1 == self.fail_on:
            self.writes.append(None)
            raise self.error
        self.writes.append(bytes(_message))

    async def disconnect(self):
        self.disconnects += 1


async def fake_connect():
    return None


async def no_sleep(_seconds):
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


async def test_beverage_start_is_not_replayed_after_a_failed_write(
    monkeypatch,
):
    monkeypatch.setattr("asyncio.sleep", no_sleep)
    client = FailingClient(2, BleakError("lost"))
    device = make_device(client)

    result = await device.send_command(
        list(MACCHIATO_START[:-2]) + [0, 0], retries=3)

    assert result is False
    # One attempt only: the first chunk and the failed second one
    assert client.writes == [MACCHIATO_START[:20], None]
    assert client.disconnects == 1


async def test_other_commands_are_still_retried(monkeypatch):
    monkeypatch.setattr("asyncio.sleep", no_sleep)
    monkeypatch.setattr("asyncio.wait_for", fake_wait_for)
    client = FailingClient(1, BleakError("lost"))
    device = make_device(client)

    async def reconnect():
        device._client = client

    device._connect = reconnect
    statistics = [0x0D, 0x08, 0xA2, 0x0F, 0x00, 0x64, 0x0A, 0x00, 0x00]

    await device.send_command(statistics, retries=2)

    assert len(client.writes) == 2
    assert client.writes[1] is not None


async def test_cancelled_mid_frame_drops_the_connection():
    client = FailingClient(2, asyncio.CancelledError())
    device = make_device(client)

    with pytest.raises(asyncio.CancelledError):
        await device.send_command(
            list(MACCHIATO_START[:-2]) + [0, 0], retries=1)

    assert client.disconnects == 1
    assert device._client is None
