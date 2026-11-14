"""Regressions for the time sync switch."""

import asyncio
import datetime
import os
import sys
import time

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
from delonghi_primadonna.switch import \
    DelongiPrimadonnaTimeSyncSwitch  # noqa: E402

CONFIG = {
    "mac": "00:11:22:33:44:55",
    "model": "TEST",
    "name": "TEST",
}


class FakeHass:
    """Runs scheduled tasks on the loop and keeps them for inspection."""

    def __init__(self):
        self.tasks = []

    def async_create_task(self, coro):
        task = asyncio.ensure_future(coro)
        self.tasks.append(task)
        return task


def make_switch(awake=True):
    device = DelongiPrimadonna(CONFIG, None)
    device.switches.is_on = awake
    # Spy on the clock command instead of sending it. clock_answers is
    # what set_time reports: False when no frame came back.
    device.clock_sets = []
    device.clock_answers = True

    async def fake_set_time(dt):
        device.clock_sets.append(dt)
        return device.clock_answers

    device.set_time = fake_set_time
    hass = FakeHass()
    switch = DelongiPrimadonnaTimeSyncSwitch(device, hass)
    switch.hass = hass
    return switch, device, hass


async def test_turn_on_enables_synchronisation():
    """Turning the switch on must actually enable syncing.

    It only ever set the clock once and left sync_time False, so the
    switch could turn synchronisation off but never on.
    """
    switch, device, _ = make_switch()

    assert device.sync_time is False
    await switch.async_turn_on()

    assert device.sync_time is True
    assert switch.is_on is True


async def test_turn_off_disables_synchronisation():
    switch, device, _ = make_switch()
    await switch.async_turn_on()

    await switch.async_turn_off()

    assert device.sync_time is False
    assert switch.is_on is False


async def test_state_follows_the_device():
    """is_on reads the device rather than a private copy."""
    switch, device, _ = make_switch()

    device.sync_time = True
    assert switch.is_on is True
    device.sync_time = False
    assert switch.is_on is False


async def test_turn_on_sets_the_clock_once():
    switch, _, hass = make_switch()

    await switch.async_turn_on()

    assert len(hass.tasks) == 1


async def test_daily_resync_waits_a_day():
    switch, device, hass = make_switch()
    await switch.async_turn_on()
    hass.tasks.clear()

    await switch.async_update()
    assert hass.tasks == [], "re-synced again immediately after turning on"

    device.last_time_sync -= 25 * 3600
    await switch.async_update()
    assert len(hass.tasks) == 1, "did not re-sync after a day"


async def test_no_resync_while_disabled():
    switch, device, hass = make_switch()
    device.sync_time = False
    device.last_time_sync -= 25 * 3600

    await switch.async_update()

    assert hass.tasks == []


async def test_switch_methods_are_coroutines():
    """HA runs sync turn_on in an executor thread, where calling
    hass.async_create_task is not thread safe."""
    switch, _, _ = make_switch()

    assert asyncio.iscoroutinefunction(switch.async_turn_on)
    assert asyncio.iscoroutinefunction(switch.async_turn_off)
    own = type(switch).__dict__
    assert "turn_on" not in own, "still defines a synchronous turn_on"
    assert "turn_off" not in own, "still defines a synchronous turn_off"


async def test_no_clock_command_while_in_standby():
    """A machine in standby does not answer the clock command.

    Measured 2026-10-17: right after a Home Assistant restart, with the
    machine in standby, the daily sync went out and drew no reply for the
    full 10 s timeout and a WARNING. Awake, the same command is answered
    in 267 ms. So the sync waits for the machine to wake up.
    """
    switch, device, hass = make_switch(awake=False)
    device.sync_time = True
    device.last_time_sync -= 25 * 3600

    await switch.async_update()
    await asyncio.gather(*hass.tasks)
    assert device.clock_sets == [], "sent the clock to a machine in standby"

    device.switches.is_on = True
    await switch.async_update()
    await asyncio.gather(*hass.tasks)
    assert len(device.clock_sets) == 1, "did not sync once the machine woke up"


async def test_turn_on_in_standby_syncs_on_wake_up():
    switch, device, hass = make_switch(awake=False)
    # Not due by the daily rule, so only the pending request can send it.
    device.last_time_sync = time.monotonic()

    await switch.async_turn_on()
    await asyncio.gather(*hass.tasks)
    assert device.sync_time is True
    assert device.clock_sets == [], "sent the clock to a machine in standby"

    device.switches.is_on = True
    await switch.async_update()
    await asyncio.gather(*hass.tasks)
    assert len(device.clock_sets) == 1, "the deferred sync was lost"


async def test_unanswered_sync_is_retried_on_next_poll():
    """A clock command that drew no frame stays pending.

    Otherwise a timeout right after wake-up would count as a sync and
    the clock would wait another day.
    """
    switch, device, hass = make_switch()
    device.last_time_sync = time.monotonic()
    device.clock_answers = False

    await switch.async_turn_on()
    await asyncio.gather(*hass.tasks)
    assert len(device.clock_sets) == 1

    device.clock_answers = True
    await switch.async_update()
    await asyncio.gather(*hass.tasks)
    assert len(device.clock_sets) == 2, "unanswered sync was not retried"

    await switch.async_update()
    await asyncio.gather(*hass.tasks)
    assert len(device.clock_sets) == 2, "answered sync was repeated"


async def test_set_time_reports_whether_a_frame_came_back():
    """The switch's retry depends on set_time passing the result on."""
    device = DelongiPrimadonna(CONFIG, None)
    for answered in (True, False):
        async def fake_send_command(message, retries=3, answered=answered):
            return answered

        device.send_command = fake_send_command
        assert await device.set_time(
            datetime.datetime(2026, 11, 14, 9, 30)
        ) is answered


async def run_tests():
    await test_turn_on_enables_synchronisation()
    await test_turn_off_disables_synchronisation()
    await test_state_follows_the_device()
    await test_turn_on_sets_the_clock_once()
    await test_daily_resync_waits_a_day()
    await test_no_resync_while_disabled()
    await test_switch_methods_are_coroutines()
    await test_no_clock_command_while_in_standby()
    await test_turn_on_in_standby_syncs_on_wake_up()
    await test_unanswered_sync_is_retried_on_next_poll()
    await test_set_time_reports_whether_a_frame_came_back()
    print("[SUCCESS] Time sync switch verified.")


if __name__ == "__main__":
    asyncio.run(run_tests())
