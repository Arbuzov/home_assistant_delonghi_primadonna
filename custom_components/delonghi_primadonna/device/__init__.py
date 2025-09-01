"""Device layer for Delonghi PrimaDonna coffee machines.

This package contains the pure business logic for communicating with the device:
- BLE transport layer
- Protocol handling  
- Message parsing
- Device abstraction

No Home Assistant dependencies here - this could be used standalone.
"""

from .ble_connection import BleConnection, BleConnectionError
from .delonghi_device import DelonghiDevice, DeviceError
from .message_protocol import MessageProtocol, ProtocolError
from .client import DelonghiPrimaDonnaClient
from .message_parser import (
    DeviceStatus,
    MessageType,
    ParsedMessage,
    ProfileData,
    MessageParser,
    StatisticsData,
)

__all__ = [
    "BleConnection",
    "BleConnectionError",
    "DelonghiDevice", 
    "DelonghiPrimaDonnaClient",
    "DeviceError",
    "DeviceStatus",
    "MessageProtocol",
    "MessageType",
    "ParsedMessage",
    "ProfileData",
    "ProtocolError",
    "MessageParser",
    "StatisticsData",
]
