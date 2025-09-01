"""Low-level BLE connection management.

This module handles only the BLE transport layer - connecting, disconnecting,
sending bytes and receiving bytes. It knows nothing about the coffee machine
protocol or Home Assistant.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Callable

from bleak import BleakClient
from bleak.exc import BleakDBusError, BleakError
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class BleConnectionError(Exception):
    """BLE connection related errors."""


class BleConnection:
    """Pure BLE transport layer without any business logic."""

    def __init__(
        self,
        mac_address: str,
        hass: HomeAssistant,
        control_characteristic: str,
        notify_characteristic: str,
    ) -> None:
        """Initialize BLE connection."""
        self._mac_address = mac_address
        self._hass = hass
        self._control_characteristic = control_characteristic
        self._notify_characteristic = notify_characteristic
        self._client: BleakClient | None = None
        self._device = None
        self._lock = asyncio.Lock()
        self._data_handlers: list[Callable[[bytes], None]] = []

    def add_data_handler(self, handler: Callable[[bytes], None]) -> None:
        """Add handler for incoming data."""
        self._data_handlers.append(handler)

    def remove_data_handler(self, handler: Callable[[bytes], None]) -> None:
        """Remove data handler."""
        if handler in self._data_handlers:
            self._data_handlers.remove(handler)

    async def connect(self, timeout: float = 10.0) -> None:
        """Connect to the BLE device."""
        async with self._lock:
            if self._client and self._client.is_connected:
                return

            self._device = bluetooth.async_ble_device_from_address(
                self._hass, self._mac_address, connectable=True
            )
            if not self._device:
                raise BleConnectionError(
                    f"Device with address {self._mac_address} not found"
                )

            self._client = BleakClient(self._device)
            
            try:
                await asyncio.wait_for(self._client.connect(), timeout=timeout)
                await asyncio.wait_for(
                    self._client.start_notify(
                        uuid.UUID(self._notify_characteristic),
                        self._on_data_received,
                    ),
                    timeout=timeout,
                )
                _LOGGER.info("Connected to %s", self._mac_address)
            except Exception as error:
                await self._cleanup_client()
                raise BleConnectionError(f"Failed to connect: {error}") from error

    async def disconnect(self) -> None:
        """Disconnect from the BLE device."""
        async with self._lock:
            await self._cleanup_client()

    async def _cleanup_client(self) -> None:
        """Clean up the BLE client."""
        if self._client:
            try:
                if self._client.is_connected:
                    await asyncio.wait_for(self._client.disconnect(), timeout=5)
            except Exception as error:
                _LOGGER.warning("Error during disconnect: %s", error)
            finally:
                self._client = None

    async def send_data(self, data: bytes, timeout: float = 10.0) -> None:
        """Send data to the device."""
        if not self._client or not self._client.is_connected:
            raise BleConnectionError("Not connected")

        try:
            await asyncio.wait_for(
                self._client.write_gatt_char(
                    self._control_characteristic, data
                ),
                timeout=timeout,
            )
        except Exception as error:
            raise BleConnectionError(f"Failed to send data: {error}") from error

    @property
    def is_connected(self) -> bool:
        """Check if connected to the device."""
        return self._client is not None and self._client.is_connected

    def _on_data_received(self, sender, data: bytes) -> None:
        """Handle incoming data from BLE."""
        for handler in self._data_handlers:
            try:
                handler(data)
            except Exception as error:
                _LOGGER.error("Error in data handler: %s", error)
