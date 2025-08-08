"""Utilities for decoding BLE messages from the PrimaDonna coffee maker.

The parsing logic here is shared by the BLE client and individual entities.
It assembles packets from the raw byte stream, interprets known
notifications and dispatches events within Home Assistant when device
state changes occur.
"""

from __future__ import annotations

import logging
import uuid
from binascii import crc_hqx, hexlify

from .const import AVAILABLE_PROFILES, DOMAIN
from .machine_switch import parse_switches
from .models import DEVICE_NOTIFICATION, DEVICE_STATUS, NOZZLE_STATE

_LOGGER = logging.getLogger(__name__)

START_BYTE = 0xD0
STAT_HEADER_SIZE = 4
STAT_RECORD_SIZE = 6
CRC_SIZE = 2
EXPECTED_PARAM_MASK = 0x0F


def parse_stat_response(resp: bytes) -> list[int]:
    """Extract integer parameters from a statistics response.

    The PrimaDonna encodes statistics as a sequence of ``address``/``value``
    pairs where each value occupies four bytes.  The response does not carry
    an explicit count of parameters; instead the length byte determines how
    many pairs follow.  This parser validates the packet structure, verifies
    the CRC and returns the list of integer values.
    """

    if (
        len(resp) < STAT_HEADER_SIZE + CRC_SIZE + STAT_RECORD_SIZE
        or resp[0] != START_BYTE
        or resp[2] != 0xA2
    ):
        raise ValueError("Invalid statistics response")

    if resp[1] + 1 != len(resp):
        raise ValueError("Mismatched statistics length")

    if resp[3] != EXPECTED_PARAM_MASK:
        raise ValueError("Unexpected statistics parameter mask")

    crc = int.from_bytes(resp[-CRC_SIZE:], "big")
    calc_crc = crc_hqx(bytearray(resp[:-CRC_SIZE]), 0x1D0F)
    if crc != calc_crc:
        raise ValueError("Statistics CRC mismatch")

    data = resp[STAT_HEADER_SIZE:-CRC_SIZE]
    if len(data) % STAT_RECORD_SIZE != 0:
        raise ValueError("Unexpected statistics payload size")

    stats: list[int] = []
    for i in range(0, len(data), STAT_RECORD_SIZE):
        # Each statistics record is STAT_RECORD_SIZE bytes.
        # The first two bytes are skipped as they are reserved or unused according to the protocol specification.
        # If the record format changes, update this logic accordingly.
        stats.append(int.from_bytes(data[i + 2:i + STAT_RECORD_SIZE], "big"))
    return stats


class MessageParser:
    """Mixin class providing common logic for packet processing.

    It contains helpers used by :class:`DelongiPrimadonna` to assemble full
    messages from fragmented notifications and to convert them into Home
    Assistant events.
    """

    _rx_buffer: bytearray
    _response_event: None
    switches: object
    steam_nozzle: str
    service: int
    status: str
    active_switches: list
    notify: bool
    mac: str
    name: str
    _hass: object
    profiles: list

    async def _event_trigger(self, value: bytes) -> None:
        """Create Home Assistant events for raw messages."""
        event_data = {"data": str(hexlify(value, " "))}
        notification_message = (
            str(hexlify(value, " "))
            .replace(" ", ", 0x")
            .replace("b'", "[0x")
            .replace("'", "]")
        )
        if str(bytearray(value)) in DEVICE_NOTIFICATION:
            note = DEVICE_NOTIFICATION[str(bytearray(value))]
            notification_message = note.description
            event_data.setdefault("type", note.kind)
            event_data.setdefault("description", note.description)
        self._hass.bus.async_fire(f"{DOMAIN}_event", event_data)
        if self.notify:
            answer_id = f"{value[2]:02x}"
            await self._hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": notification_message,
                    "title": f"{self.name} {answer_id}",
                    "notification_id": f"{self.mac}_err_{uuid.uuid4()}",
                },
            )
        _LOGGER.info("Event triggered: %s", event_data)

    async def _process_raw_data(self, sender, value: bytes) -> None:
        """Assemble incoming BLE packets and pass complete messages."""
        self._rx_buffer.extend(value)
        while True:
            if len(self._rx_buffer) < 2:
                return
            try:
                start_index = self._rx_buffer.index(START_BYTE)
            except ValueError:
                self._rx_buffer.clear()
                return
            if start_index > 0:
                del self._rx_buffer[:start_index]
            if len(self._rx_buffer) < 2:
                return
            msg_len = self._rx_buffer[1] + 1
            if len(self._rx_buffer) < msg_len:
                return
            packet = bytes(self._rx_buffer[:msg_len])
            del self._rx_buffer[:msg_len]
            await self._handle_data(sender, packet)

    async def _handle_data(self, sender, value: bytes) -> None:
        """Handle notifications from the device."""
        if (
            self._response_event is not None
            and not self._response_event.is_set()
        ):
            self._last_response = value
            self._response_event.set()
        answer_id = value[2] if len(value) > 2 else None
        if answer_id == 0x75:
            self.switches.is_on = value[9] > 0
            self.steam_nozzle = NOZZLE_STATE.get(value[4], value[4])
            self.service = value[7]
            self.status = DEVICE_STATUS.get(value[5], DEVICE_STATUS[5])
            self.active_switches = parse_switches(value)
        elif answer_id == 0xA4:
            parsed = []
            try:
                parsed = self._parse_profile_response(list(value))
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Failed to parse profile response: %s", err)
            for pid, name in parsed.items():
                AVAILABLE_PROFILES[pid] = name
            _LOGGER.debug("Available profiles: %s", AVAILABLE_PROFILES)
            self.profiles = list(AVAILABLE_PROFILES.values())
        elif answer_id == 0xA9:
            profile_id = value[4] if len(value) > 4 else None
            status = value[5] if len(value) > 5 else None
            _LOGGER.debug(
                "Profile change response id=%s status=%s raw=%s",
                profile_id,
                status,
                hexlify(value, " "),
            )
        elif answer_id == 0xA2:
            stats = []
            try:
                stats = parse_stat_response(value)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Failed to parse statistics response: %s", err)
            _LOGGER.info("Machine statistics: %s", stats)
        hex_value = hexlify(value, " ")
        if getattr(self, "_device_status", None) != hex_value:
            _LOGGER.info("Received data: %s from %s", hex_value, sender)
            await self._event_trigger(value)
            self._device_status = hex_value

    def _parse_profile_response(self, data: list[int]) -> dict[int, str]:
        """Parse profile names sent by the machine."""
        b = bytes(data)
        if len(b) < 4 or b[0] != 0xD0:
            raise ValueError("Wrong start byte")
        profiles: dict[int, str] = {}
        NAME_SIZE = 20
        NAME_OFFSET = 1
        NAME_HEADER = 4
        profile_index = 1
        idx = NAME_HEADER
        while idx + NAME_SIZE < len(b):
            profiles[profile_index] = (
                b[idx : idx + NAME_SIZE]  # noqa: E203
                .decode("utf-16-be")
                .rstrip("\x00")
                .strip()
            )  # noqa: E203
            profile_index += 1
            idx += NAME_SIZE + NAME_OFFSET
        return profiles
