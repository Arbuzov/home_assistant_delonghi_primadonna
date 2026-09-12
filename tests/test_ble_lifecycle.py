import asyncio
import os
import sys
import time

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

import delonghi_primadonna.device as device_module  # noqa: E402
from delonghi_primadonna.const import BYTES_STATISTICS_COMMAND  # noqa: E402
from delonghi_primadonna.device import DelongiPrimadonna  # noqa: E402
from delonghi_primadonna.device_tracker import \
    DelongiPrimadonnaDeviceTracker  # noqa: E402

CONFIG = {
    "mac": "00:11:22:33:44:55",
    "model": "TEST",
    "name": "TEST",
}


def make_device(hass=None):
    return DelongiPrimadonna(CONFIG, hass)


class FakeBus:
    def __init__(self):
        self.events = []

    def async_fire(self, event_type, data=None):
        self.events.append((event_type, data))


class FakeHass:
    def __init__(self):
        self.created_tasks = []
        self.background_tasks = []
        self.bus = FakeBus()

    def async_create_task(self, coro):
        task = asyncio.create_task(coro)
        self.created_tasks.append(task)
        return task

    def async_create_background_task(self, coro, _name):
        task = asyncio.create_task(coro)
        self.background_tasks.append(task)
        return task


class FakeConnectClient:
    def __init__(
        self,
        *,
        notify_error=None,
        block_notify=False,
    ):
        self.is_connected = True
        self.notify_error = notify_error
        self.block_notify = block_notify
        self.notify_started = asyncio.Event()
        self.notify_release = asyncio.Event()
        self.start_notify_calls = 0
        self.disconnect_calls = 0

    async def start_notify(self, _characteristic, _callback):
        self.start_notify_calls += 1
        self.notify_started.set()

        if self.notify_error is not None:
            raise self.notify_error

        if self.block_notify:
            await self.notify_release.wait()

    async def disconnect(self):
        self.disconnect_calls += 1
        self.is_connected = False


class FailingWriteClient:
    is_connected = True

    def __init__(self):
        self.disconnect_calls = 0

    async def write_gatt_char(
        self,
        _characteristic,
        _message,
    ):
        raise BleakError("write failed")

    async def disconnect(self):
        self.disconnect_calls += 1
        self.is_connected = False


async def run_with_fake_connection(device, client):
    original_lookup = (
        device_module.bluetooth.async_ble_device_from_address
    )
    original_establish = device_module.establish_connection

    fake_ble_device = object()

    def fake_lookup(_hass, _mac, connectable):
        assert connectable is True
        return fake_ble_device

    async def fake_establish(
        _client_class,
        ble_device,
        _name,
        max_attempts,
    ):
        assert ble_device is fake_ble_device
        assert max_attempts == 3
        return client

    device_module.bluetooth.async_ble_device_from_address = (
        fake_lookup
    )
    device_module.establish_connection = fake_establish

    try:
        await device._connect()
    finally:
        device_module.bluetooth.async_ble_device_from_address = (
            original_lookup
        )
        device_module.establish_connection = original_establish


async def test_connect_success():
    device = make_device()
    client = FakeConnectClient()

    await run_with_fake_connection(device, client)

    assert device._client is client
    assert device.connected is True
    assert client.start_notify_calls == 1
    assert client.disconnect_calls == 0
    assert device._connecting is False


async def test_connect_clears_receive_buffer_before_notifications():
    device = make_device()
    device._rx_buffer.extend(
        b"\\xd0\\x41\\xa2\\x0f\\x00"
    )
    client = FakeConnectClient()

    observed_buffer = None
    original_start_notify = client.start_notify

    async def inspecting_start_notify(
        characteristic,
        callback,
    ):
        nonlocal observed_buffer
        observed_buffer = bytes(device._rx_buffer)
        await original_start_notify(
            characteristic,
            callback,
        )

    client.start_notify = inspecting_start_notify

    await run_with_fake_connection(device, client)

    assert observed_buffer == b""
    assert device._rx_buffer == bytearray()


RX_TEST_PACKET = bytes.fromhex(
    "d0 41 a2 0f 00 64 2d 34 3b 42 49 50 57 5e 65 6c "
    "73 7a 81 88 8f 96 9d a4 ab b2 b9 c0 c7 ce d5 dc "
    "e3 ea f1 f8 ff 06 0d 14 1b 22 29 30 37 3e 45 4c "
    "53 5a 61 68 6f 76 7d 84 8b 92 99 a0 a7 ae b5 bc "
    "05 97"
)


async def test_receive_buffer_reassembles_fragmented_packet():
    device = make_device()
    handled_packets = []

    async def capture_packet(_sender, packet):
        handled_packets.append(bytes(packet))

    device._handle_data = capture_packet

    await device._process_raw_data(None, RX_TEST_PACKET[:20])

    assert handled_packets == []
    assert device._rx_buffer == bytearray(RX_TEST_PACKET[:20])

    await device._process_raw_data(None, RX_TEST_PACKET[20:])

    assert handled_packets == [RX_TEST_PACKET]
    assert device._rx_buffer == bytearray()


async def test_receive_buffer_discards_invalid_crc_packet():
    device = make_device()
    handled_packets = []

    assert device._has_valid_crc(RX_TEST_PACKET)

    corrupted_packet = bytearray(RX_TEST_PACKET)
    corrupted_packet[-1] ^= 0x01
    corrupted_packet = bytes(corrupted_packet)

    assert not device._has_valid_crc(corrupted_packet)

    device._expected_statistics_start = 100
    device._response_event = asyncio.Event()

    async def no_event(_value):
        return None

    device._event_trigger = no_event

    original_handle_data = device._handle_data

    async def capture_and_handle(sender, packet):
        handled_packets.append(bytes(packet))
        await original_handle_data(sender, packet)

    device._handle_data = capture_and_handle

    await device._process_raw_data(None, corrupted_packet)

    assert handled_packets == []
    assert not device._response_event.is_set()
    assert not device.statistics
    assert device._rx_buffer == bytearray()


async def test_receive_buffer_recovers_from_restarted_frame():
    device = make_device()
    handled_packets = []

    async def capture_packet(_sender, packet):
        handled_packets.append(bytes(packet))

    device._handle_data = capture_packet

    await device._process_raw_data(None, RX_TEST_PACKET[:20])

    assert handled_packets == []

    # Reproduce the live failure: after a 20-byte partial packet, the
    # device restarts transmission from the beginning of the same frame.
    await device._process_raw_data(None, RX_TEST_PACKET)

    assert handled_packets == [RX_TEST_PACKET]
    assert device._rx_buffer == bytearray()


async def test_notify_failure_disconnects_client():
    device = make_device()
    client = FakeConnectClient(
        notify_error=BleakError("notify failed")
    )

    try:
        await run_with_fake_connection(device, client)
    except BleakError:
        pass
    else:
        raise AssertionError(
            "_connect did not propagate start_notify failure"
        )

    assert client.disconnect_calls == 1
    assert device._client is None
    assert device.connected is False
    assert device._connecting is False


async def test_connect_cancellation_disconnects_client():
    device = make_device()
    client = FakeConnectClient(block_notify=True)

    original_lookup = (
        device_module.bluetooth.async_ble_device_from_address
    )
    original_establish = device_module.establish_connection

    fake_ble_device = object()

    def fake_lookup(_hass, _mac, connectable):
        assert connectable is True
        return fake_ble_device

    async def fake_establish(
        _client_class,
        ble_device,
        _name,
        max_attempts,
    ):
        assert ble_device is fake_ble_device
        assert max_attempts == 3
        return client

    device_module.bluetooth.async_ble_device_from_address = (
        fake_lookup
    )
    device_module.establish_connection = fake_establish

    task = asyncio.create_task(device._connect())

    try:
        await client.notify_started.wait()

        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass
        else:
            raise AssertionError(
                "_connect did not propagate cancellation"
            )
    finally:
        device_module.bluetooth.async_ble_device_from_address = (
            original_lookup
        )
        device_module.establish_connection = original_establish

    assert client.disconnect_calls == 1
    assert device._client is None
    assert device._connecting is False


async def test_write_bleak_error_disconnects_client():
    device = make_device()
    client = FailingWriteClient()
    device._client = client

    async def fake_connect():
        return None

    device._connect = fake_connect

    original_sleep = device_module.asyncio.sleep

    async def no_sleep(_delay):
        return None

    device_module.asyncio.sleep = no_sleep

    try:
        result = await device.send_command(
            list(BYTES_STATISTICS_COMMAND),
            retries=1,
        )
    finally:
        device_module.asyncio.sleep = original_sleep

    assert result is False
    assert client.disconnect_calls == 1
    assert device._client is None
    assert device.connected is False


async def test_initialization_task_is_cancelled_and_awaited():
    device = make_device()

    started = asyncio.Event()
    cleaned_up = asyncio.Event()

    async def initialization():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaned_up.set()

    task = asyncio.create_task(initialization())
    device.set_initialization_task(task)

    await started.wait()
    await device.cancel_initialization()

    assert device._initialization_task is None
    assert task.cancelled()
    assert cleaned_up.is_set()


async def test_get_device_name_propagates_cancellation():
    device = make_device()

    async def cancelled_connect():
        raise asyncio.CancelledError

    device._connect = cancelled_connect

    try:
        await device.get_device_name()
    except asyncio.CancelledError:
        pass
    else:
        raise AssertionError(
            "get_device_name swallowed cancellation"
        )

    assert device.connected is False


class FakeTrackerDevice:
    def __init__(self):
        self.calls = 0
        self.started = asyncio.Event()

    async def get_device_name(self):
        self.calls += 1
        self.started.set()
        await asyncio.Event().wait()


async def test_tracker_deduplicates_and_cancels_update():
    hass = FakeHass()
    fake_device = FakeTrackerDevice()

    tracker = DelongiPrimadonnaDeviceTracker.__new__(
        DelongiPrimadonnaDeviceTracker
    )
    tracker.hass = hass
    tracker.device = fake_device
    tracker._device_name_task = None

    await tracker.async_update()
    first_task = tracker._device_name_task

    await tracker.async_update()
    second_task = tracker._device_name_task

    await fake_device.started.wait()

    assert first_task is second_task
    assert fake_device.calls == 1
    assert hass.created_tasks == []
    assert len(hass.background_tasks) == 1

    await tracker.async_will_remove_from_hass()

    assert tracker._device_name_task is None
    assert first_task.cancelled()


async def test_statistics_task_deduplicates_and_cancels():
    hass = FakeHass()
    device = make_device(hass)

    calls = 0
    started = asyncio.Event()

    async def statistics_update():
        nonlocal calls
        calls += 1
        started.set()
        await asyncio.Event().wait()

    device.update_statistics = statistics_update
    device._last_stats_request = 0.0

    device.schedule_statistics_update()
    first_task = device._statistics_task

    device.schedule_statistics_update()
    second_task = device._statistics_task

    await started.wait()

    assert first_task is second_task
    assert calls == 1
    assert hass.created_tasks == []
    assert len(hass.background_tasks) == 1

    await device.cancel_statistics_update()

    assert device._statistics_task is None
    assert first_task.cancelled()


async def test_failed_statistics_attempt_is_throttled():
    hass = FakeHass()
    device = make_device(hass)
    calls = []

    async def failed_statistics(start_index, count):
        calls.append((start_index, count))
        return False

    device.get_statistics = failed_statistics
    device._last_stats_request = 0.0

    before = time.monotonic()
    await device.update_statistics()
    after = time.monotonic()

    assert calls == [(100, 10)]
    assert before <= device._last_stats_request <= after

    device.schedule_statistics_update()

    assert device._statistics_task is None
    assert hass.background_tasks == []


async def test_statistics_update_exception_is_contained_and_reschedulable():
    hass = FakeHass()
    device = make_device(hass)
    calls = 0

    async def failing_statistics_update():
        nonlocal calls
        calls += 1
        raise RuntimeError("statistics failed")

    device.update_statistics = failing_statistics_update
    device._last_stats_request = 0.0

    device.schedule_statistics_update()
    first_task = device._statistics_task

    assert first_task is not None

    await first_task

    assert first_task.done()
    assert not first_task.cancelled()
    assert device._statistics_task is first_task
    assert calls == 1

    device.schedule_statistics_update()
    second_task = device._statistics_task

    assert second_task is not None
    assert second_task is not first_task

    await second_task

    assert second_task.done()
    assert not second_task.cancelled()
    assert device._statistics_task is second_task
    assert calls == 2
    assert len(hass.background_tasks) == 2


async def test_statistics_schedule_respects_throttle():
    hass = FakeHass()
    device = make_device(hass)

    device._last_stats_request = time.monotonic()

    device.schedule_statistics_update()

    assert device._statistics_task is None
    assert hass.created_tasks == []


def make_profile_response(names):
    """Build a 0xA4 profile-response frame.

    Header is [0xD0, len, 0xA4, 0xF0] as the parser expects, then one
    slot per profile of 20 name bytes (UTF-16-BE, NUL-terminated)
    followed by a 1-byte icon (per #265 the response carries no index;
    the parser maps slots positionally, so this byte's value is ignored).

    Test-only helper, not the wire format: the length byte follows the
    msg_len == total - 1 convention, but there is no CRC, so the real
    ingest CRC gate would park the frame and the tests deliver it
    straight to _handle_data.
    """
    body = bytearray([0xD0, 0x00, 0xA4, 0xF0])
    for pid in sorted(names):
        name = names[pid].encode("utf-16-be")[:20]
        body += name.ljust(20, b"\x00")
        body += bytes([pid])
    body[1] = len(body) - 1
    return bytes(body)


async def test_profiles_isolated_between_devices():
    dev_a = make_device(FakeHass())
    dev_b = make_device(FakeHass())

    await dev_a._handle_data(None, make_profile_response({
        1: "Anna",
        2: "Bob",
    }))
    await asyncio.sleep(0)

    await dev_b._handle_data(None, make_profile_response({
        1: "Cathy",
        2: "Dan",
    }))
    await asyncio.sleep(0)

    # Each device must reflect only the names it received, and the
    # module-level AVAILABLE_PROFILES must never leak across instances.
    assert dev_a.profiles[0] == "Anna"
    assert dev_a.profiles[1] == "Bob"
    assert dev_b.profiles[0] == "Cathy"
    assert dev_b.profiles[1] == "Dan"
    assert dev_a.profiles != dev_b.profiles

    # Defaults for slots that were not present in the frame survive.
    assert dev_a.profiles[2] == "Profile 3"
    assert dev_a.profiles[3] == "Guest"


async def run_tests():
    await test_profiles_isolated_between_devices()
    await test_connect_success()
    await test_connect_clears_receive_buffer_before_notifications()
    await test_receive_buffer_reassembles_fragmented_packet()
    await test_receive_buffer_discards_invalid_crc_packet()
    await test_receive_buffer_recovers_from_restarted_frame()
    await test_notify_failure_disconnects_client()
    await test_connect_cancellation_disconnects_client()
    await test_write_bleak_error_disconnects_client()

    await test_initialization_task_is_cancelled_and_awaited()
    await test_get_device_name_propagates_cancellation()
    await test_tracker_deduplicates_and_cancels_update()

    await test_statistics_task_deduplicates_and_cancels()
    await test_failed_statistics_attempt_is_throttled()
    await test_statistics_update_exception_is_contained_and_reschedulable()
    await test_statistics_schedule_respects_throttle()

    print(
        "[SUCCESS] BLE lifecycle regressions "
        "for commits 1-3 verified."
    )


if __name__ == "__main__":
    asyncio.run(run_tests())
