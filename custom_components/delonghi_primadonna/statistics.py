"""Helpers for querying machine statistical parameters."""

from __future__ import annotations

from typing import Protocol

from .const import STATISTICS_PARAM_MASK


class _CommandSender(Protocol):
    """Protocol representing the BLE client used for communication."""

    async def send_command(self, message: list[int]) -> bytes | None:
        """Send a command to the device."""


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
    """Read statistical parameters from the coffee machine."""

    def __init__(self, ble_device: _CommandSender) -> None:
        """Initialize the reader with a BLE client."""
        self._ble = ble_device

    def _make_request(self, addr: int, count: int) -> list[int]:
        """Form packet for ``getStatisticalParameters`` (0xA2)."""

        count = min(count, 10)
        packet = [
            0x0D,
            8,
            0xA2,
            STATISTICS_PARAM_MASK,
            addr >> 8,
            addr & 0xFF,
            count,
            0x00,
            0x00,
        ]
        return packet

    async def read_all(self) -> None:
        """Send requests for all blocks."""

        for addr, qty in BLOCKS:
            packet = self._make_request(addr, qty)
            await self._ble.send_command(packet)
