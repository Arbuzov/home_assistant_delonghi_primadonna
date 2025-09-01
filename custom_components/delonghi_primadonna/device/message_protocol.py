"""Delonghi PrimaDonna message protocol implementation.

This module handles the coffee machine specific protocol:
- Message framing and CRC calculation
- Command preparation 
- Response parsing
- No business logic or Home Assistant dependencies
"""

from __future__ import annotations

import asyncio
import copy
import logging
from binascii import crc_hqx, hexlify
from typing import Callable

_LOGGER = logging.getLogger(__name__)

START_BYTE = 0xD0


class ProtocolError(Exception):
    """Protocol related errors."""


class MessageProtocol:
    """Handles Delonghi PrimaDonna protocol specifics."""

    def __init__(self) -> None:
        """Initialize protocol handler."""
        self._rx_buffer = bytearray()
        self._message_handlers: list[Callable[[bytes], None]] = []

    def add_message_handler(self, handler: Callable[[bytes], None]) -> None:
        """Add handler for complete messages."""
        self._message_handlers.append(handler)

    def remove_message_handler(self, handler: Callable[[bytes], None]) -> None:
        """Remove message handler."""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)

    def prepare_command(self, command: list[int]) -> bytes:
        """Prepare command with CRC."""
        message = copy.deepcopy(command)
        if len(message) < 2:
            raise ProtocolError("Command too short")
        
        # Calculate CRC for all bytes except the last 2 (CRC placeholder)
        crc = crc_hqx(bytearray(message[:-2]), 0x1D0F)
        crc_bytes = crc.to_bytes(2, byteorder="big")
        message[-2] = crc_bytes[0]
        message[-1] = crc_bytes[1]
        
        return bytes(message)

    def handle_raw_data(self, data: bytes) -> None:
        """Process incoming raw BLE data and extract complete messages."""
        self._rx_buffer.extend(data)
        
        while True:
            if len(self._rx_buffer) < 2:
                return
                
            # Find start byte
            try:
                start_index = self._rx_buffer.index(START_BYTE)
            except ValueError:
                self._rx_buffer.clear()
                return
                
            if start_index > 0:
                del self._rx_buffer[:start_index]
                
            if len(self._rx_buffer) < 2:
                return
                
            # Check if we have complete message
            msg_len = self._rx_buffer[1] + 1
            if len(self._rx_buffer) < msg_len:
                return
                
            # Extract complete message
            message = bytes(self._rx_buffer[:msg_len])
            del self._rx_buffer[:msg_len]
            
            # Validate message
            if self._validate_message(message):
                self._dispatch_message(message)
            else:
                _LOGGER.warning("Invalid message received: %s", hexlify(message))

    def _validate_message(self, message: bytes) -> bool:
        """Validate message structure and CRC."""
        if len(message) < 4:
            return False
            
        if message[0] != START_BYTE:
            return False
            
        # For responses that have CRC, validate it
        if len(message) >= 4 and message[2] in [0x75, 0xA2, 0xA4, 0xA9]:
            try:
                expected_crc = int.from_bytes(message[-2:], "big")
                calculated_crc = crc_hqx(bytearray(message[:-2]), 0x1D0F)
                return expected_crc == calculated_crc
            except Exception:
                return False
                
        return True

    def _dispatch_message(self, message: bytes) -> None:
        """Send complete message to all handlers."""
        for handler in self._message_handlers:
            try:
                handler(message)
            except Exception as error:
                _LOGGER.error("Error in message handler: %s", error)
