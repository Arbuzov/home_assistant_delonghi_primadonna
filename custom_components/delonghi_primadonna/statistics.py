"""Helpers for querying machine statistical parameters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .const import BYTES_STATISTICS_REQUEST

if TYPE_CHECKING:
    from .ble_client import DelongiPrimadonna


# (address, number of parameters) pairs to request from the device.
BLOCKS: list[tuple[int, int]] = [
    (160, 10),
    (170, 10),
    (180, 10),
    (150, 10),
    (190, 4),
    (110, 10),
    (120, 10),
    (130, 10),
    (140, 10),
    (100, 10),
    (50, 10),
    (60, 7),
    (200, 10),
    (250, 9),
]


class StatisticsReader:
    """Handle requesting statistical parameters from the machine."""

    def __init__(self, ble_device: "DelongiPrimadonna") -> None:
        """Initialize the reader with a BLE client."""
        self._ble = ble_device

    def _make_request(self, addr: int, count: int) -> list[int]:
        """Form packet for ``getStatisticalParameters`` (0xA2)."""

        packet = BYTES_STATISTICS_REQUEST.copy()
        packet[4] = addr >> 8
        packet[5] = addr & 0xFF
        packet[6] = min(count, 10)
        return packet

    async def request_all(self) -> None:
        """Send requests for all blocks."""

        for addr, qty in BLOCKS:
            packet = self._make_request(addr, qty)
            await self._ble.send_command(packet)
