"""The status sensor must reflect the state table."""

import asyncio
import os
import sys

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
from delonghi_primadonna.device import parse_monitor_data  # noqa: E402

CONFIG = {
    "mac": "00:11:22:33:44:55",
    "model": "TEST",
    "name": "TEST",
}


def monitor_v2(status: int) -> bytes:
    data = bytearray(16)
    data[0] = 0xD0
    data[1] = 0x12
    data[2] = 0x75
    data[9] = status
    return bytes(data)


def status_for(state: int) -> str:
    device = DelongiPrimadonna(CONFIG, None)
    packet = monitor_v2(state)
    device._handle_monitor_data(parse_monitor_data(packet), 0x75, packet)
    return device.status


async def test_measured_states():
    """Measured on an ECAM 656.55.MS during a full descaling run."""
    assert status_for(4) == "descaling"
    assert status_for(5) == "delivering_steam"
    assert status_for(14) == "changing_filter"
    assert status_for(12) == "cleaning_milk_spout"


async def test_off_and_heating_are_not_reported_as_ready():
    """A branch above the table claimed Ready for 0, 1 and 5."""
    assert status_for(0) == "turned_off"
    assert status_for(1) == "heating"


async def test_status_2_is_shutting_down_not_washing():
    """Status 2 appears right after the power-off command.

    Measured on an ECAM 656.55.MS: ready at 19:31:23, power off sent at
    19:31:30, status 2 at 19:31:35 and nothing resembling a rinse.
    """
    assert status_for(2) == "shutting_down"


async def test_ready_still_reports_ready():
    assert status_for(7) == "ready"


async def run_tests():
    await test_measured_states()
    await test_off_and_heating_are_not_reported_as_ready()
    await test_status_2_is_shutting_down_not_washing()
    await test_ready_still_reports_ready()
    print("[SUCCESS] Machine states verified.")


if __name__ == "__main__":
    asyncio.run(run_tests())
