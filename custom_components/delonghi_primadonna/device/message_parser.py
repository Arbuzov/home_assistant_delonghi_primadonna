"""Pure message parser for Delonghi PrimaDonna messages.

This module only parses messages into structured data.
No Home Assistant dependencies, no side effects.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

_LOGGER = logging.getLogger(__name__)

STAT_HEADER_SIZE = 4
STAT_RECORD_SIZE = 6
CRC_SIZE = 2
EXPECTED_PARAM_MASK = 0x0F


class MessageType(Enum):
    """Known message types."""
    STATUS = 0x75
    STATISTICS = 0xA2
    PROFILE_DATA = 0xA4
    PROFILE_CHANGE = 0xA9
    UNKNOWN = 0xFF


@dataclass
class DeviceStatus:
    """Parsed device status."""
    is_powered: bool
    nozzle_state: int
    service_counter: int
    device_status: int
    alarms: list[int]
    raw_data: bytes


@dataclass
class ProfileData:
    """Parsed profile information."""
    profiles: dict[int, str]
    raw_data: bytes


@dataclass
class StatisticsData:
    """Parsed statistics."""
    values: list[int]
    raw_data: bytes


@dataclass
class ParsedMessage:
    """Container for parsed message data."""
    message_type: MessageType
    data: Any
    raw_message: bytes


class MessageParserError(Exception):
    """Parser related errors."""


class MessageParser:
    """Pure message parser without any dependencies."""

    def parse_message(self, message: bytes) -> ParsedMessage:
        """Parse a complete message into structured data."""
        if len(message) < 3:
            raise MessageParserError("Message too short")

        message_id = message[2]
        
        if message_id == 0x75:
            return ParsedMessage(
                MessageType.STATUS,
                self._parse_status_message(message),
                message
            )
        elif message_id == 0xA2:
            return ParsedMessage(
                MessageType.STATISTICS,
                self._parse_statistics_message(message),
                message
            )
        elif message_id == 0xA4:
            return ParsedMessage(
                MessageType.PROFILE_DATA,
                self._parse_profile_message(message),
                message
            )
        elif message_id == 0xA9:
            return ParsedMessage(
                MessageType.PROFILE_CHANGE,
                self._parse_profile_change_message(message),
                message
            )
        else:
            return ParsedMessage(
                MessageType.UNKNOWN,
                {"raw": message.hex()},
                message
            )

    def _parse_status_message(self, message: bytes) -> DeviceStatus:
        """Parse device status message."""
        if len(message) < 10:
            raise MessageParserError("Status message too short")

        return DeviceStatus(
            is_powered=message[9] > 0 if len(message) > 9 else False,
            nozzle_state=message[4] if len(message) > 4 else 0,
            service_counter=message[7] if len(message) > 7 else 0,
            device_status=message[5] if len(message) > 5 else 0,
            alarms=self._parse_alarm_bits(message),
            raw_data=message
        )

    def _parse_alarm_bits(self, message: bytes) -> list[int]:
        """Parse alarm bits from status message."""
        if len(message) < 8:
            return []

        mask = message[5] | (message[7] << 8)
        
        # Handle duplicate grounds container flags
        if len(message) > 7 and message[7] & 0x08:
            mask &= ~(1 << 2)
            mask &= ~(1 << 9)

        active_alarms = []
        for bit in range(16):
            if mask & (1 << bit):
                active_alarms.append(bit)
                
        return active_alarms

    def _parse_profile_message(self, message: bytes) -> ProfileData:
        """Parse profile names from message."""
        if len(message) < 4 or message[0] != 0xD0:
            raise MessageParserError("Invalid profile message")

        profiles = {}
        NAME_SIZE = 20
        NAME_OFFSET = 1
        NAME_HEADER = 4
        profile_index = 1
        idx = NAME_HEADER

        while idx + NAME_SIZE <= len(message):
            try:
                profile_name = (
                    message[idx:idx + NAME_SIZE]
                    .decode("utf-16-be")
                    .rstrip("\x00")
                    .strip()
                )
                if profile_name:  # Only add non-empty names
                    profiles[profile_index] = profile_name
                profile_index += 1
                idx += NAME_SIZE + NAME_OFFSET
            except UnicodeDecodeError as error:
                _LOGGER.warning("Failed to decode profile name: %s", error)
                break

        return ProfileData(profiles=profiles, raw_data=message)

    def _parse_profile_change_message(self, message: bytes) -> dict[str, Any]:
        """Parse profile change confirmation."""
        return {
            "profile_id": message[4] if len(message) > 4 else None,
            "status": message[5] if len(message) > 5 else None,
        }

    def _parse_statistics_message(self, message: bytes) -> StatisticsData:
        """Parse statistics response."""
        if (
            len(message) < STAT_HEADER_SIZE + CRC_SIZE + STAT_RECORD_SIZE
            or message[0] != 0xD0
            or message[2] != 0xA2
        ):
            raise MessageParserError("Invalid statistics message")

        if message[1] + 1 != len(message):
            raise MessageParserError("Statistics length mismatch")

        if message[3] != EXPECTED_PARAM_MASK:
            raise MessageParserError("Unexpected statistics parameter mask")

        data = message[STAT_HEADER_SIZE:-CRC_SIZE]
        if len(data) % STAT_RECORD_SIZE != 0:
            raise MessageParserError("Invalid statistics payload size")

        stats = []
        for i in range(0, len(data), STAT_RECORD_SIZE):
            # Skip first 2 bytes of each record, read the 4-byte value
            value = int.from_bytes(data[i + 2:i + STAT_RECORD_SIZE], "big")
            stats.append(value)

        return StatisticsData(values=stats, raw_data=message)
