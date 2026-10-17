import asyncio
import os
import sys
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
from delonghi_primadonna.const import BYTES_STATISTICS_COMMAND  # noqa: E402
from delonghi_primadonna.device import DelongiPrimadonna  # noqa: E402

CONFIG = {
    "mac": "00:11:22:33:44:55",
    "model": "TEST",
    "name": "TEST",
}

LOG_PACKET = unhexlify(
    "d041a20f00640013a89e00650000000a"
    "00690000000f006a002365e8006c0000"
    "0000006d00000000006f000000120074"
    "000002840284000000000bb80000397e"
    "54d1"
)


SPARSE_111_PACKET = unhexlify(
    "d041a20f006f000000110074000000c9"
    "00c90000001f0bb800000c570bb90000"
    "00980bba0000007c0bbb000000030bbc"
    "000000230bbd000000230bbe00000089"
    "1941"
)


def make_device():
    return DelongiPrimadonna(CONFIG, None)


async def no_event(_value):
    return None


def statistics_message(start_index=100, count=10):
    message = list(BYTES_STATISTICS_COMMAND)
    message[4] = (start_index >> 8) & 0xFF
    message[5] = start_index & 0xFF
    message[6] = count
    return message


async def test_matching_statistics_response():
    device = make_device()
    device._expected_statistics_start = 100
    device._response_event = asyncio.Event()
    device._device_status = hexlify(LOG_PACKET, " ")
    device._event_trigger = no_event

    await device._handle_data(None, LOG_PACKET)

    assert device._response_event.is_set()
    assert device.statistics[100] == 1288350
    assert device.statistics[105] == 15


async def test_wrong_statistics_start_is_ignored():
    device = make_device()
    device._expected_statistics_start = 110
    device._response_event = asyncio.Event()
    device._device_status = hexlify(LOG_PACKET, " ")
    device._event_trigger = no_event

    await device._handle_data(None, LOG_PACKET)

    assert not device._response_event.is_set()
    assert 100 not in device.statistics
    assert 105 not in device.statistics


async def test_sparse_statistics_response_matches_111():
    device = make_device()
    device._expected_statistics_start = 111
    device._response_event = asyncio.Event()
    device._device_status = hexlify(SPARSE_111_PACKET, " ")
    device._event_trigger = no_event

    assert device._has_valid_crc(SPARSE_111_PACKET)

    await device._process_raw_data(None, SPARSE_111_PACKET)

    assert device._response_event.is_set()
    assert device.statistics[111] == 17
    assert device.statistics[116] == 201
    assert device.statistics[3000] == 3159
    assert device.statistics[3006] == 137


async def test_sparse_statistics_response_advances_from_110_to_111():
    device = make_device()
    device._expected_statistics_start = 110
    device._response_event = asyncio.Event()
    device._device_status = hexlify(SPARSE_111_PACKET, " ")
    device._event_trigger = no_event

    assert device._has_valid_crc(SPARSE_111_PACKET)

    await device._process_raw_data(None, SPARSE_111_PACKET)

    assert device._response_event.is_set()
    assert device.statistics[111] == 17
    assert device.statistics[116] == 201


async def test_sparse_statistics_response_advances_from_3077_to_23000():
    device = make_device()
    packet = bytes.fromhex(
        "d0 1d a2 0f 59 d8 00 00 00 07 "
        "59 d9 00 00 26 d0 "
        "59 da 00 00 00 69 "
        "59 db 00 00 01 92 "
        "00 ce"
    )
    device._expected_statistics_start = 3077
    device._response_event = asyncio.Event()
    device._device_status = hexlify(packet, " ")
    device._event_trigger = no_event

    assert device._has_valid_crc(packet)

    await device._process_raw_data(None, packet)

    assert device._response_event.is_set()
    assert device.statistics[23000] == 7
    assert device.statistics[23001] == 9936
    assert device.statistics[23003] == 402
    assert 3077 not in device.statistics


async def test_short_statistics_response_is_ignored():
    device = make_device()
    packet = bytes(
        [0xD0, 0x05, 0xA2, 0x0F, 0x00, 0x64]
    )

    device._expected_statistics_start = 100
    device._response_event = asyncio.Event()
    device._device_status = hexlify(packet, " ")
    device._event_trigger = no_event

    await device._handle_data(None, packet)

    assert not device._response_event.is_set()
    assert not device.statistics


async def test_stale_statistics_response_is_ignored():
    device = make_device()
    device._expected_statistics_start = None
    device._response_event = asyncio.Event()
    device._device_status = hexlify(LOG_PACKET, " ")
    device._event_trigger = no_event

    await device._handle_data(None, LOG_PACKET)

    assert not device._response_event.is_set()
    assert not device.statistics


async def test_monitor_packet_does_not_release_statistics_waiter():
    device = make_device()
    packet = bytes([0xD0, 0x02, 0x70])

    device._expected_statistics_start = 100
    device._response_event = asyncio.Event()
    device._device_status = hexlify(packet, " ")
    device._event_trigger = no_event

    original_parser = device_module.parse_monitor_data
    device_module.parse_monitor_data = lambda _value: None
    try:
        await device._handle_data(None, packet)
    finally:
        device_module.parse_monitor_data = original_parser

    assert not device._response_event.is_set()


class FakeClient:
    is_connected = True

    async def write_gatt_char(
        self,
        _characteristic,
        _message,
    ):
        return None


class RespondingFakeClient:
    is_connected = True

    def __init__(self, device, response):
        self._device = device
        self._response = response
        self.last_message = None

    async def write_gatt_char(
        self,
        _characteristic,
        _message,
    ):
        self.last_message = bytes(_message)
        await self._device._handle_data(
            None,
            self._response,
        )


async def fake_connect():
    return None


async def test_matching_statistics_command_returns_true():
    device = make_device()
    device._device_status = hexlify(LOG_PACKET, " ")
    device._client = RespondingFakeClient(
        device,
        LOG_PACKET,
    )
    device._connect = fake_connect

    result = await device.send_command(
        statistics_message(),
        retries=1,
    )

    assert result is True
    assert device.statistics[100] == 1288350
    assert device.statistics[105] == 15
    assert device._response_event is None
    assert device._expected_statistics_start is None


async def test_matching_sparse_statistics_command_returns_true():
    device = make_device()
    device._device_status = hexlify(SPARSE_111_PACKET, " ")
    client = RespondingFakeClient(
        device,
        SPARSE_111_PACKET,
    )
    device._client = client
    device._connect = fake_connect

    result = await device.send_command(
        statistics_message(111),
        retries=1,
    )

    assert result is True
    assert client.last_message == unhexlify(
        "0d08a20f006f0aff6d"
    )
    assert device.statistics[111] == 17
    assert device.statistics[3000] == 3159
    assert device._response_event is None
    assert device._expected_statistics_start is None


async def test_non_statistics_command_returns_true():
    device = make_device()
    response = bytes([0xD0, 0x02, 0x84])
    device._device_status = hexlify(response, " ")
    device._client = RespondingFakeClient(
        device,
        response,
    )
    device._connect = fake_connect

    result = await device.send_command(
        [
            0x0D,
            0x07,
            0x84,
            0x0F,
            0x02,
            0x01,
            0x00,
            0x00,
        ],
        retries=1,
    )

    assert result is True
    assert device._response_event is None
    assert device._expected_statistics_start is None


async def test_timeout_clears_pending_response_state():
    device = make_device()
    device._client = FakeClient()
    device._connect = fake_connect

    original_wait_for = device_module.asyncio.wait_for

    async def immediate_timeout(awaitable, timeout):
        del timeout
        close = getattr(awaitable, "close", None)
        if close is not None:
            close()
        raise asyncio.TimeoutError

    device_module.asyncio.wait_for = immediate_timeout
    try:
        result = await device.send_command(
            statistics_message(),
            retries=1,
        )
    finally:
        device_module.asyncio.wait_for = original_wait_for

    assert result is False
    assert device._response_event is None
    assert device._expected_statistics_start is None


async def test_cancellation_clears_pending_response_state():
    device = make_device()
    device._client = FakeClient()
    device._connect = fake_connect

    task = asyncio.create_task(
        device.send_command(
            statistics_message(),
            retries=1,
        )
    )

    for _ in range(20):
        if device._response_event is not None:
            break
        await asyncio.sleep(0)

    assert device._response_event is not None

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass
    else:
        raise AssertionError(
            "send_command did not propagate cancellation"
        )

    assert device._response_event is None
    assert device._expected_statistics_start is None


async def test_failed_first_range_aborts_statistics_batch():
    device = make_device()
    calls = []

    async def failed_statistics(start_index, count):
        calls.append((start_index, count))
        return False

    device.get_statistics = failed_statistics

    await device.update_statistics()

    assert calls == [(100, 10)]


async def test_statistics_polling_starts_second_block_at_110():
    device = make_device()
    calls = []

    async def successful_statistics(start_index, count):
        calls.append((start_index, count))
        return True

    async def no_sleep(_delay):
        return None

    device.get_statistics = successful_statistics
    device._last_stats_request = (
        device_module.time.monotonic() - 61
    )

    original_sleep = device_module.asyncio.sleep
    device_module.asyncio.sleep = no_sleep
    try:
        await device.update_statistics()
    finally:
        device_module.asyncio.sleep = original_sleep

    assert calls == [
        (100, 10),
        (110, 10),
        (3000, 10),
        (3017, 10),
        (3077, 4),
    ]


async def run_tests():
    await test_matching_statistics_response()
    await test_wrong_statistics_start_is_ignored()
    await test_sparse_statistics_response_matches_111()
    await test_sparse_statistics_response_advances_from_110_to_111()
    await test_sparse_statistics_response_advances_from_3077_to_23000()
    await test_short_statistics_response_is_ignored()
    await test_stale_statistics_response_is_ignored()
    await test_monitor_packet_does_not_release_statistics_waiter()
    await test_matching_statistics_command_returns_true()
    await test_matching_sparse_statistics_command_returns_true()
    await test_non_statistics_command_returns_true()
    await test_timeout_clears_pending_response_state()
    await test_cancellation_clears_pending_response_state()
    await test_failed_first_range_aborts_statistics_batch()
    await test_statistics_polling_starts_second_block_at_110()

    print(
        "[SUCCESS] BLE response correlation "
        "regressions verified."
    )


if __name__ == "__main__":
    asyncio.run(run_tests())
