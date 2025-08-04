"""Helpers for querying machine statistical parameters."""

from __future__ import annotations

from binascii import crc_hqx

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
    (250, 9),  # 250 = ImageRequest.DEFAULT_IMAGE_TIMEOUT_MS
]


def make_stat_request(addr: int, count: int) -> list[int]:
    """Form a packet for the ``getStatisticalParameters`` command (0xA2)."""

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


def parse_stat_response(resp: bytes) -> list[int]:
    """Validate CRC and extract integer parameters from the response."""

    if crc_hqx(bytearray(resp[:-2]), 0x1D0F) != int.from_bytes(resp[-2:], "big"):
        raise ValueError("CRC mismatch")

    count = resp[6]
    data = resp[7 : 7 + count * 2]
    return [int.from_bytes(data[i : i + 2], "big") for i in range(0, len(data), 2)]


async def read_all_stats(ble_device: DelongiPrimadonna) -> list[int]:
    """Send requests for all blocks and collect responses."""

    result: list[int] = []
    for addr, qty in BLOCKS:
        packet = make_stat_request(addr, qty)
        resp = await ble_device.send_command(packet)
        if resp is not None:
            result.extend(parse_stat_response(resp))
    return result

