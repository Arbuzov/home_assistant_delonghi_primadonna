"""Delonghi PrimaDonna device abstraction.

This module contains the business logic for interacting with the coffee machine.
It uses the lower-level components but doesn't know about Home Assistant.
"""

from __future__ import annotations

import asyncio
import copy
import logging
from datetime import datetime
from typing import Callable

from .ble_connection import BleConnection, BleConnectionError
from .message_protocol import MessageProtocol, ProtocolError
from .message_parser import (
    MessageType,
    ParsedMessage,
    MessageParser,
    DeviceStatus,
    ProfileData,
    StatisticsData,
)

_LOGGER = logging.getLogger(__name__)


class DeviceError(Exception):
    """Device operation errors."""


class DelonghiDevice:
    """High-level interface to Delonghi PrimaDonna coffee machine."""

    def __init__(
        self,
        mac_address: str,
        control_characteristic: str,
        notify_characteristic: str,
        connection: BleConnection,
    ) -> None:
        """Initialize device."""
        self.mac_address = mac_address
        self._connection = connection
        self._protocol = MessageProtocol()
        self._parser = MessageParser()
        
        # Device state
        self._current_status: DeviceStatus | None = None
        self._profiles: dict[int, str] = {}
        self._statistics: list[int] = []
        
        # Event handlers
        self._status_handlers: list[Callable[[DeviceStatus], None]] = []
        self._profile_handlers: list[Callable[[dict[int, str]], None]] = []
        self._statistics_handlers: list[Callable[[list[int]], None]] = []
        
        # Response handling
        self._response_events: dict[int, asyncio.Event] = {}
        self._last_responses: dict[int, ParsedMessage] = {}
        
        # Wire up the pipeline
        self._connection.add_data_handler(self._protocol.handle_raw_data)
        self._protocol.add_message_handler(self._handle_parsed_message)

    async def connect(self, retries: int = 3) -> None:
        """Connect to the device with retries."""
        last_error = None
        
        for attempt in range(retries):
            try:
                await self._connection.connect()
                _LOGGER.info("Connected to device %s", self.mac_address)
                return
            except BleConnectionError as error:
                _LOGGER.warning(
                    "Connection attempt %d failed: %s", attempt + 1, error
                )
                last_error = error
                if attempt < retries - 1:
                    await asyncio.sleep(2)
        
        raise DeviceError(f"Failed to connect after {retries} attempts") from last_error

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        await self._connection.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connection.is_connected

    @property
    def current_status(self) -> DeviceStatus | None:
        """Get current device status."""
        return self._current_status

    @property
    def profiles(self) -> dict[int, str]:
        """Get available profiles."""
        return self._profiles.copy()

    @property
    def statistics(self) -> list[int]:
        """Get current statistics."""
        return self._statistics.copy()

    # Event handler management
    def add_status_handler(self, handler: Callable[[DeviceStatus], None]) -> None:
        """Add handler for status updates."""
        self._status_handlers.append(handler)

    def add_profile_handler(self, handler: Callable[[dict[int, str]], None]) -> None:
        """Add handler for profile updates."""
        self._profile_handlers.append(handler)

    def add_statistics_handler(self, handler: Callable[[list[int]], None]) -> None:
        """Add handler for statistics updates."""
        self._statistics_handlers.append(handler)

    async def send_command(
        self, 
        command: list[int], 
        wait_for_response: bool = True,
        timeout: float = 10.0
    ) -> ParsedMessage | None:
        """Send a command to the device."""
        if not self.is_connected:
            raise DeviceError("Not connected to device")

        try:
            # Prepare command with protocol
            prepared_data = self._protocol.prepare_command(command)
            
            # Set up response waiting if needed
            response_event = None
            if wait_for_response and len(command) > 2:
                expected_response_id = command[2]  # Assuming response has same ID
                response_event = asyncio.Event()
                self._response_events[expected_response_id] = response_event

            # Send command
            await self._connection.send_data(prepared_data)
            _LOGGER.debug("Sent command: %s", prepared_data.hex())

            # Wait for response if requested
            if response_event:
                try:
                    await asyncio.wait_for(response_event.wait(), timeout=timeout)
                    return self._last_responses.pop(expected_response_id, None)
                except asyncio.TimeoutError:
                    _LOGGER.warning("Timeout waiting for response to command")
                    return None
                finally:
                    self._response_events.pop(expected_response_id, None)

        except (BleConnectionError, ProtocolError) as error:
            raise DeviceError(f"Failed to send command: {error}") from error

        return None

    def _handle_parsed_message(self, message: bytes) -> None:
        """Handle incoming parsed messages."""
        try:
            parsed = self._parser.parse_message(message)
            
            # Update internal state and notify handlers
            if parsed.message_type == MessageType.STATUS:
                self._current_status = parsed.data
                self._notify_status_handlers(parsed.data)
                
            elif parsed.message_type == MessageType.PROFILE_DATA:
                self._profiles.update(parsed.data.profiles)
                self._notify_profile_handlers(self._profiles)
                
            elif parsed.message_type == MessageType.STATISTICS:
                self._statistics = parsed.data.values
                self._notify_statistics_handlers(self._statistics)

            # Handle response events
            if len(message) > 2:
                response_id = message[2]
                if response_id in self._response_events:
                    self._last_responses[response_id] = parsed
                    self._response_events[response_id].set()

        except Exception as error:
            _LOGGER.error("Error handling message: %s", error)

    def _notify_status_handlers(self, status: DeviceStatus) -> None:
        """Notify all status handlers."""
        for handler in self._status_handlers:
            try:
                handler(status)
            except Exception as error:
                _LOGGER.error("Error in status handler: %s", error)

    def _notify_profile_handlers(self, profiles: dict[int, str]) -> None:
        """Notify all profile handlers."""
        for handler in self._profile_handlers:
            try:
                handler(profiles)
            except Exception as error:
                _LOGGER.error("Error in profile handler: %s", error)

    def _notify_statistics_handlers(self, statistics: list[int]) -> None:
        """Notify all statistics handlers."""
        for handler in self._statistics_handlers:
            try:
                handler(statistics)
            except Exception as error:
                _LOGGER.error("Error in statistics handler: %s", error)

    # High-level device operations
    async def power_on(self) -> None:
        """Turn on the device."""
        # This would use actual command constants from your const.py
        await self.send_command([0x0D, 0x06, 0xA9, 0xF0, 0x01, 0xD7, 0xC0])

    async def set_profile(self, profile_id: int) -> None:
        """Set active profile."""
        command = [0x0D, 0x06, 0xA9, 0xF0, profile_id, 0xD7, 0xC0]
        await self.send_command(command)

    async def set_time(self, dt: datetime) -> None:
        """Set device clock."""
        # This would use actual time command from your const.py
        command = [0x0D, 0x06, 0xA3, 0x10, dt.hour, dt.minute, 0x00, 0x00]
        await self.send_command(command)

    async def request_statistics(self) -> None:
        """Request device statistics."""
        # This would iterate through your STATISTICS_BLOCKS
        command = [0x0D, 0x08, 0xA2, 0x0F, 0x00, 0x00, 0x0A, 0x00, 0x00]
        await self.send_command(command)
