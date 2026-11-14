"""Custom recipes start with the quantities stored on the machine (#286)."""

import asyncio
import os
import sys
from binascii import crc_hqx

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
        )
    )
)

from delonghi_primadonna.device import (  # noqa: E402
    DelongiPrimadonna, _build_recipe_read_command,
    _build_recipe_start_command, _parse_recipe_quantity)

# PrimaDonna S Evo: Custom 1 is recipe 230 and has no quantities in
# MachinesModels.json.
CONFIG = {
    "mac": "00:11:22:33:44:55",
    "model": "0132215355",
    "name": "TEST",
}


def with_crc(frame):
    crc = crc_hqx(bytes(frame[:-2]), 0x1D0F)
    return bytes(frame[:-2]) + crc.to_bytes(2, "big")


def recipe_answer(profile, recipe_id, body):
    frame = [0xD0, 0x00, 0xA6, 0xF0, profile, recipe_id, *body, 0, 0]
    frame[1] = len(frame) - 1
    return with_crc(frame)


# temp 2, coffee 40 ml, taste 4, inversion 0, visible 1, accessory 0
EXTRAPRESSO = [0x00, 0x02, 0x01, 0x00, 0x28, 0x02, 0x04,
               0x0C, 0x00, 0x19, 0x01, 0x1C, 0x00]


def test_read_command():
    assert _build_recipe_read_command(1, 230)[:6] == [
        0x0D, 0x07, 0xA6, 0xF0, 0x01, 0xE6
    ]


def test_parse_recipe_answer():
    profile, recipe_id, ingredients = _parse_recipe_quantity(
        recipe_answer(1, 230, EXTRAPRESSO)
    )
    assert (profile, recipe_id) == (1, 230)
    assert ingredients == [
        (0x00, 2), (0x01, 40), (0x02, 4), (0x0C, 0), (0x19, 1), (0x1C, 0),
    ]


def test_parse_rejects_unknown_tag_and_truncated_value():
    assert _parse_recipe_quantity(recipe_answer(1, 230, [0x30, 0x01])) is None
    assert _parse_recipe_quantity(recipe_answer(1, 230, [0x01, 0x00])) is None


def test_start_frame_matches_coffee_link_layout():
    """Same layout as the app's Espresso Macchiato in DEBUG_NOTES."""
    ingredients = [
        (0x1C, 2), (0x00, 2), (0x01, 79), (0x02, 3), (0x04, 0),
        (0x09, 82), (0x0B, 1), (0x19, 1),
    ]
    frame = _build_recipe_start_command(0x0B, ingredients, profile=1)
    assert frame[:-2] == [
        0x0D, 0x18, 0x83, 0xF0, 0x0B, 0x01,
        0x00, 0x02, 0x01, 0x00, 0x4F, 0x02, 0x03, 0x04, 0x00,
        0x09, 0x00, 0x52, 0x0B, 0x01, 0x1C, 0x02, 0x06,
    ]
    assert frame[1] == len(frame) - 1


def test_profile_goes_into_last_byte():
    frame = _build_recipe_start_command(230, [(0x01, 40)], profile=2)
    assert frame[-3] == (2 << 2) | 2


class FakeHass:
    def async_create_background_task(self, coro, name):
        return asyncio.get_running_loop().create_task(coro)


async def test_custom_start_uses_stored_quantities():
    device = DelongiPrimadonna(CONFIG, FakeHass())
    sent = []

    async def send_command(message, retries=3):
        sent.append(list(message))
        if message[2] == 0xA6:
            await device._handle_data(
                None, recipe_answer(message[4], message[5], EXTRAPRESSO)
            )
        return True

    async def no_event(value):
        return None

    device.send_command = send_command
    device._event_trigger = no_event

    await device.beverage_start("Custom 1")

    assert sent[0][:6] == [0x0D, 0x07, 0xA6, 0xF0, 0x01, 0xE6]
    start = sent[1]
    assert start[2:6] == [0x83, 0xF0, 0xE6, 0x01]
    # coffee 40 ml, not 0
    assert start[8:11] == [0x01, 0x00, 0x28]
    # metadata (visible) is not sent, accessory is last
    assert 0x19 not in start[6:-3:2]
    assert start[-5:-3] == [0x1C, 0x00]
    assert len(start) <= 20
    assert device.cooking == "Custom 1"


async def test_custom_start_falls_back_without_answer():
    device = DelongiPrimadonna(CONFIG, FakeHass())
    sent = []

    async def send_command(message, retries=3):
        sent.append(list(message))
        return True

    device.send_command = send_command

    task = asyncio.ensure_future(device.beverage_start("Custom 1"))
    await asyncio.wait_for(task, 5)

    assert sent[0][2] == 0xA6
    assert sent[1][:6] == [0x0D, 0x0D, 0x83, 0xF0, 0xE6, 0x01]


async def test_standard_recipe_does_not_read_the_machine():
    device = DelongiPrimadonna(CONFIG, FakeHass())
    sent = []

    async def send_command(message, retries=3):
        sent.append(list(message))
        return True

    device.send_command = send_command
    await device.beverage_start("Espresso Coffee")

    assert len(sent) == 1
    assert sent[0][2] == 0x83
