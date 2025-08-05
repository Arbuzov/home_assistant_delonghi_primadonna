"""Helpers for querying machine statistical parameters."""

from __future__ import annotations

import logging
from binascii import crc_hqx
from typing import Protocol

LOGGER = logging.getLogger(__name__)


class _CommandSender(Protocol):
    """Protocol representing the BLE client used for communication."""

    async def send_command(self, message: list[int]) -> bytes | None:
        """Send a command to the device and return the raw response."""


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
            0x0F,
            addr >> 8,
            addr & 0xFF,
            count,
            0x00,
            0x00,
        ]
        return packet

    def _parse_response(self, resp: bytes) -> list[int]:
        """Validate CRC and extract integer parameters from the response."""

        if len(resp) < 9:
            raise ValueError("Response too short")

        if crc_hqx(bytearray(resp[:-2]), CRC16_CCITT_INITIAL) != int.from_bytes(
            resp[-2:], "big"
        ):
            raise ValueError("CRC mismatch")

        count = resp[6]
        expected = 7 + count * 2 + 2
        if len(resp) < expected:
            raise ValueError("Incomplete response")

        data = resp[7:7 + count * 2]
        return [
            int.from_bytes(data[i:i + 2], "big")
            for i in range(0, len(data), 2)
        ]

    async def read_all(self) -> list[int]:
        """Send requests for all blocks and collect responses."""

        result: list[int] = []
        for addr, qty in BLOCKS:
            packet = self._make_request(addr, qty)
            resp = await self._ble.send_command(packet)
            if resp is None:
                LOGGER.warning("No response for statistical block %s", addr)
                continue
            result.extend(self._parse_response(resp))
        return result
