"""Regressions for matching a BLE reply to the request it answers."""

import asyncio
import os
import sys
import time
from binascii import hexlify, unhexlify

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
        )
    )
)

import delonghi_primadonna.device as device_module  # noqa: E402
from delonghi_primadonna.device import DelongiPrimadonna  # noqa: E402

CONFIG = {
    "mac": "00:11:22:33:44:55",
    "model": "TEST",
    "name": "TEST",
}


def make_device():
    return DelongiPrimadonna(CONFIG, None)


async def no_event(_value):
    return None


class FakeClient:
    is_connected = True

    async def write_gatt_char(self, _characteristic, _message):
        return None


async def fake_connect():
    return None


async def test_foreign_answer_id_does_not_release_waiter():
    """A status frame must not satisfy a wait for a different command.

    Unsolicited 0x75 status frames arrive every few seconds while the
    machine is awake. Releasing any pending wait on them attributes a
    reply to whatever command happened to be in flight.
    """
    device = make_device()
    status_frame = bytes([0xD0, 0x02, 0x75])

    device._expected_answer_id = 0x95
    device._response_event = asyncio.Event()
    device._device_status = hexlify(status_frame, " ")
    device._event_trigger = no_event

    original_parser = device_module.parse_monitor_data
    device_module.parse_monitor_data = lambda _value: None
    try:
        await device._handle_data(None, status_frame)
    finally:
        device_module.parse_monitor_data = original_parser

    assert not device._response_event.is_set()


async def test_matching_answer_id_releases_waiter():
    """The reply carries the request id, which is what identifies it."""
    device = make_device()
    reply = unhexlify("d00b950f003d00000001bd2d")

    device._expected_answer_id = 0x95
    device._response_event = asyncio.Event()
    device._device_status = hexlify(reply, " ")
    device._event_trigger = no_event

    await device._handle_data(None, reply)

    assert device._response_event.is_set()


async def test_power_command_does_not_wait_for_a_reply():
    """The machine never answers 0x84, so waiting only blocks the lock."""
    device = make_device()
    device._client = FakeClient()
    device._connect = fake_connect

    started = time.monotonic()
    await device.send_command(
        [0x0D, 0x07, 0x84, 0x0F, 0x02, 0x01, 0x00, 0x00],
        retries=1,
    )
    elapsed = time.monotonic() - started

    assert elapsed < 1, f"waited {elapsed:.1f}s for a reply that never comes"
    assert device._response_event is None
    assert device._expected_answer_id is None


async def run_tests():
    await test_foreign_answer_id_does_not_release_waiter()
    await test_matching_answer_id_releases_waiter()
    await test_power_command_does_not_wait_for_a_reply()
    print("[SUCCESS] BLE response correlation verified.")


if __name__ == "__main__":
    asyncio.run(run_tests())
