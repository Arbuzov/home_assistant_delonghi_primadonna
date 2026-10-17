"""Constants for the oiot integration."""
from homeassistant.const import EntityCategory

DOMAIN = 'delonghi_primadonna'

DEFAULT_DEVICE_NAME = 'DeLonghi PrimaDonna'

BEVERAGE_NONE = 'none'

SERVICE = '00035b03-58e6-07dd-021a-08123a000300'

CONTROLL_CHARACTERISTIC = '00035b03-58e6-07dd-021a-08123a000301'

NAME_CHARACTERISTIC = '00002A00-0000-1000-8000-00805F9B34FB'

DESCRIPTOR = '00002902-0000-1000-8000-00805f9b34fb'

DEFAULT_IMAGE_URL = (
    'https://delonghibe.s3.eu-west-1.amazonaws.com/cms/prod/img/'
    '_opt_delonghi_uploads_PD_CLASS_TOP_INT_ECAM550.85.MS.png'
)

BEVERAGE_SERVICE_NAME = 'make_beverage'

# Mapping of profile id to profile name
AVAILABLE_PROFILES = {
    1: 'Profile 1',
    2: 'Profile 2',
    3: 'Profile 3',
    4: 'Guest',
}

POWER_OFF_OPTIONS = {
    '15min': 0,
    '30min': 1,
    '1h': 2,
    '2h': 3,
    '3h': 4
}

ENTITY_CATEGORY = {
    'None': None,
    'Configuration': EntityCategory.CONFIG,
    'Diagnostic': EntityCategory.DIAGNOSTIC,
}

NOZZLE_STATE = {
    -1: "unknown",
    0: "detached",
    1: "steam",
    2: "milk_frother",
    3: "milk_frother_cleaning",
    4: "carafe_needs_cleaning",
    6: "chocolate_container",
    7: "chocolate_container_needs_cleaning",
}

# Skipable maintanence states
SERVICE_STATE = {0: 'OK', 4: 'DESCALING'}

# Alarm bit -> translation key. These are keys, not display text:
# the matching entries already live in strings.json and
# translations/*.json under entity.sensor.device_status.state.
DEVICE_STATUS = {
    0: "empty_water_tank",
    1: "coffee_waste_container_full",
    2: "descale_alarm",
    3: "replace_water_filter",
    4: "coffee_ground_too_fine",
    5: "coffee_beans_empty",
    6: "machine_to_service",
    7: "coffee_heater_probe_failure",
    8: "too_much_coffee",
    9: "coffee_infuser_motor_not_working",
    10: "steamer_probe_failure",
    11: "empty_drip_tray",
    12: "hydraulic_circuit_problem",
    13: "tank_is_in_position",
    14: "clean_knob",
    15: "coffee_beans_empty_two",
    16: "tank_too_full",
    17: "bean_hopper_absent",
    18: "grid_presence",
    19: "infuser_sense",
    20: "not_enough_coffee",
    21: "expansion_comm_prob",
    22: "expansion_submodules_prob",
    23: "grinding_unit_1_problem",
    24: "grinding_unit_2_problem",
    25: "condense_fan_problem",
    26: "clock_bt_comm_problem",
    27: "spi_comm_problem",
    99: "unknown_alarm",
}

MACHINE_STATUS = {
    0: "turned_off",
    1: "heating",
    # Measured 2026-08-20: status 2 appears immediately after the
    # power-off command, matching longshot's ShuttingDown.
    2: "shutting_down",
    3: "heating",
    # Measured on an ECAM 656.55.MS during a full descaling run, 2026-08-22.
    # 4 is set as soon as the descaling program is armed and stays set while
    # pumping, so it is the program state rather than "descaling right now".
    4: "descaling",
    # 96 s steam dispense with a full progress curve in byte 11. Mapping this
    # to "ready" made the sensor report an idle machine while steam ran.
    5: "delivering_steam",
    6: "brewing",
    7: "ready",  # v2 Ready
    8: "rinsing",
    10: "preparing",
    11: "delivering_hot_water",
    12: "cleaning_milk_spout",
    # Rinse cycle after confirming a filter change. The machine treats this
    # as its own program, not a phase of descaling.
    14: "changing_filter",
}

"""
Command bytes
"""
# Command type lives in byte 2. Used to name a command in log messages,
# so a timeout says what failed instead of only dumping its bytes.
COMMAND_NAMES = {
    0x75: 'status poll',
    0x83: 'beverage',
    0x84: 'power',
    0x90: 'write setting',
    0x95: 'read setting',
    0xA2: 'statistics',
    0xA4: 'profile names',
    0xA9: 'profile selection',
    0xE2: 'clock',
}

BYTES_POWER = [0x0d, 0x07, 0x84, 0x0f, 0x02, 0x01, 0x55, 0x12]

# AppControl (0x84) with (1, 1) puts the machine into standby. This is not
# part of the observed app traffic; it was found by probing and confirmed on
# the machines listed below. The switch is only offered for those, because
# what (1, 1) does on an untested model is unknown.
BYTES_POWER_OFF = [0x0d, 0x07, 0x84, 0x0f, 0x01, 0x01, 0x00, 0x00]

# Machine families with at least one owner report of the standby command
# working, from issue #222 where it was found. Each family rests on a
# single such report - not every code below has been confirmed
# individually. Sibling codes ride along only when MachinesModels.json
# gives them the same `type` as the reported machine, which is the
# catalog's own machine identifier; the display `name` is not enough,
# since several distinct machines share one name.
#
# Standby is not universal: Dinamica PLUS 370.95 was reported in the same
# thread as not responding to it. Hence an allow list, not a feature flag.
STANDBY_VERIFIED_PRODUCT_CODES = (
    # PrimaDonna ELITE 656.55 - these two came with the original switch in
    # #253, whose author verified them. Their types do differ (ECAM 656.55
    # protocol 2 and ECAM 656.55.MS protocol 1), so they are grandfathered
    # on that author's report rather than by the type rule above.
    '0132217031', '0132217027',
    # PrimaDonna S 510.55 - reported by the author of #222. These five all
    # carry type ECAM 510.55.M. A sixth entry, '0132215355', shares the
    # display name but its type is ECAM516.45.MB, a different machine, so
    # it is deliberately left out.
    '0132215311', '0132215322', '0132215329',
    '0132215331', '0132215339',
    # PrimaDonna ELITE 650.85 - confirmed in #222 for an ECAM650.85.MS.
    # MachinesModels.json also carries a '650.85.MS' entry under product
    # code '71234567', which is plainly a placeholder rather than a real
    # SKU, so it is left out until someone reports picking it and the
    # switch working.
    '0132219009', '0132219012', '0132219017', '0132219019',
    # Maestosa / EPAM960.75.GLM - confirmed in #222. Eight entries carry a
    # Maestosa name and the name field alone cannot tell them apart; the
    # machine identity is only in each entry's image_url. Seven of the
    # eight are EPAM960.75.GLM / MAESTOSA_BEST and these six are those,
    # minus '0132268004' - which is the same machine identity but listed
    # separately as MAESTOSA CN for the Chinese market, and is left out
    # only because no report has come from that variant. The eighth,
    # '0132267000' (MAESTOSA_GOOD), is an EPAM960.55.GM: a genuinely
    # different machine that nobody has reported standby on.
    '0132268000', '0132230018', 'J013200730',
    '0132268001', '0132268002', '0132268003',
)

# Default bitmask for commands
BASE_COMMAND = '10000001'

BYTES_TIME_COMMAND = [
    0x0d, 0x07, 0xE2, 0xF0, 0x00, 0x00, 0x00, 0x00
]

# This command change device switches
BYTES_SWITCH_COMMAND = [
    0x0d, 0x0b, 0x90, 0x0f, 0x00, 0x3f,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00
]

BYTES_AUTOPOWEROFF_COMMAND = [
    0x0d, 0x0b, 0x90, 0x0f, 0x00, 0x3e,
    0x00, 0x00, 0x00, 0x00, 0x81, 0xe3
]

BYTES_WATER_HARDNESS_COMMAND = [
    0x0d, 0x0b, 0x90, 0x0f, 0x00, 0x32,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00
]

BYTES_WATER_TEMPERATURE_COMMAND = [
    0x0d, 0x0b, 0x90, 0x0f, 0x00, 0x3d,
    0x00, 0x00, 0x00, 0x00, 0x6f, 0x31
]

# Reads a device parameter (0x95). Parameter 0x3f holds the settings
# bitmask written by BYTES_SWITCH_COMMAND (see SWITCH_BIT_* below).
PARAM_SWITCHES = 0x3F
BYTES_LOAD_SWITCHES = [
    0x0d, 0x08, 0x95, 0x0f, 0x00, 0x3f,
    0x01, 0x00, 0x00
]

# Bit layout of the settings parameter 0x3f
SWITCH_BIT_SOUNDS = 0x04
SWITCH_BIT_CUP_LIGHT = 0x08
SWITCH_BIT_ENERGY_SAVE = 0x10

BYTES_STATISTICS_COMMAND = [
    0x0d, 0x08, 0xa2, 0x0f, 0x00, 0x64,
    0x0a, 0x00, 0x00
]

# Commands that load user profiles from the device. They must be
# executed once after the first successful connection. The CRC
# bytes are zeros as they are calculated at runtime.
BYTES_LOAD_PROFILES = [0x0d, 0x07, 0xa4, 0xf0, 0x01, 0x06, 0x00, 0x00]
BYTES_LOAD_PROFILES_1 = [0x0d, 0x07, 0xa4, 0xf0, 0x01, 0x03, 0x00, 0x00]
BYTES_LOAD_PROFILES_2 = [0x0d, 0x07, 0xa4, 0xf0, 0x04, 0x06, 0x00, 0x00]

COFFE_ON = [0x0d, 0x0f, 0x83, 0xf0, 0x02, 0x01, 0x01,
            0x00, 0x67, 0x02, 0x02, 0x00, 0x00, 0x06, 0x77, 0xff]
COFFE_OFF = [0x0d, 0x08, 0x83, 0xf0, 0x02, 0x02, 0x06, 0xc4, 0xb1]

DOPPIO_ON = [0x0d, 0x0d, 0x83, 0xf0, 0x05, 0x01, 0x01,
             0x00, 0x78, 0x00, 0x00, 0x06, 0xc4, 0x7e]
DOPPIO_OFF = [0x0d, 0x08, 0x83, 0xf0, 0x05, 0x02, 0x06, 0x41, 0x21]

STEAM_ON = [0x0d, 0x0d, 0x83, 0xf0, 0x11, 0x01,
            0x09, 0x03, 0x84, 0x1c, 0x01, 0x06, 0xc0, 0x7b]
STEAM_OFF = [0x0d, 0x08, 0x83, 0xf0, 0x11, 0x02, 0x06, 0xde, 0x82]

HOTWATER_ON = [0x0d, 0x0d, 0x83, 0xf0, 0x10, 0x01,
               0x0f, 0x00, 0xfa, 0x1c, 0x01, 0x06, 0x04, 0xb4]
HOTWATER_OFF = [0x0d, 0x08, 0x83, 0xf0, 0x10, 0x02, 0x06, 0xe9, 0xb2]

ESPRESSO2_ON = [0x0d, 0x0f, 0x83, 0xf0, 0x04, 0x01, 0x01,
                0x00, 0x28, 0x02, 0x02, 0x00, 0x00, 0x06, 0xab, 0x53]
ESPRESSO2_OFF = [0x0d, 0x08, 0x83, 0xf0, 0x04, 0x02, 0x06, 0x76, 0x11]

AMERICANO_ON = [0x0d, 0x12, 0x83, 0xf0, 0x06, 0x01, 0x01, 0x00,
                0x28, 0x02, 0x03, 0x0f, 0x00, 0x6e, 0x00, 0x00,
                0x06, 0x47, 0x8b]
AMERICANO_OFF = [0x0d, 0x08, 0x83, 0xf0, 0x06, 0x02, 0x06, 0x18, 0x71]

LONG_ON = [0x0d, 0x0f, 0x83, 0xf0, 0x03, 0x01, 0x01,
           0x00, 0xa0, 0x02, 0x03, 0x00, 0x00, 0x06, 0x18, 0x7f]
LONG_OFF = [0x0d, 0x08, 0x83, 0xf0, 0x03, 0x02, 0x06, 0xf3, 0x81]

# Espresso x1 (Aroma=3 Temperature=2 Qty=40)
ESPRESSO_ON = [0x0d, 0x11, 0x83, 0xf0, 0x01, 0x01, 0x01, 0x00,
               0x28, 0x02, 0x03, 0x08, 0x00, 0x00, 0x00, 0x06, 0x8f, 0xfc]
ESPRESSO_OFF = [0x0d, 0x08, 0x83, 0xf0, 0x01, 0x02, 0x06, 0x9d, 0xe1]

# This commands return the current device state
DEBUG = [0x0d, 0x05, 0x75, 0x0f, 0xda, 0x25]

"""
Status bytes
"""
WATER_TANK_DETACHED = [0xd0, 0x12, 0x75, 0x0f, 0x01, 0x15, 0x00, 0x00,
                       0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                       0xaa, 0x31]

WATER_SHORTAGE = [0xd0, 0x12, 0x75, 0x0f, 0x01, 0x45, 0x00, 0x01, 0x00,
                  0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2f, 0x64]

WATER_SHORTAGE2 = [0xd0, 0x12, 0x75, 0x0f, 0x01, 0x41, 0x00, 0x05, 0x00,
                   0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0x4e]

GRAINS_SHORTAGE = []

CRAINS_COVER_OPENED = []

COFFEE_GROUNDS_CONTAINER_FULL = [0xd0, 0x12, 0x75, 0x0f, 0x01, 0x05, 0x00,
                                 0x02, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00,
                                 0x00, 0x00, 0x00, 0x43, 0xd0]

# On some devices the grounds container clean notification includes an
# additional bit in the general notification field. Handle it as the same
# "GroundsContainerFull" status.
COFFEE_GROUNDS_CONTAINER_CLEAN = [
    0xd0, 0x12, 0x75, 0x0f, 0x01, 0x05, 0x00, 0x0a, 0x00, 0x07, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x09, 0xa0
]

COFFEE_GROUNDS_CONTAINER_DETACHED = [0xd0, 0x12, 0x75, 0x0f, 0x01, 0x0d, 0x00,
                                     0x00, 0x00, 0x07, 0x00, 0x00,
                                     0x00, 0x00, 0x00, 0x00, 0x00, 0x86, 0xc9]

DEVICE_READY = [0xd0, 0x12, 0x75, 0x0f, 0x01, 0x05, 0x00, 0x00,
                0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x9d, 0x61]

DEVICE_TURNOFF = [0xd0, 0x12, 0x75, 0x0f, 0x01, 0x01, 0x00, 0x00,
                  0x00, 0x00, 0x03, 0x64, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0xd6, 0x96]

START_COFFEE = [0xd0, 0x12, 0x75, 0x0f, 0x01, 0x05, 0x00, 0x00,
                0x00, 0x07, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x5c, 0xa7]
