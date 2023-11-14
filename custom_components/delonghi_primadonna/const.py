"""Constants for the oiot integration."""
from homeassistant.const import EntityCategory

DOMAIN = 'delonghi_primadonna'

SERVICE = '00035b03-58e6-07dd-021a-08123a000300'

CONTROLL_CHARACTERISTIC = '00035b03-58e6-07dd-021a-08123a000301'

NAME_CHARACTERISTIC = '00002A00-0000-1000-8000-00805F9B34FB'

DESCRIPTOR = '00002902-0000-1000-8000-00805f9b34fb'

BEVERAGE_SERVICE_NAME = 'make_beverage'

AVAILABLE_PROFILES = {
    'Profile 1': 1,
    'Profile 2': 2,
    'Profile 3': 3,
    'Guest': 4
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

"""
Command bytes
"""
BYTES_POWER = [0x0d, 0x07, 0x84, 0x0f, 0x02, 0x01, 0x55, 0x12]

# Default bitmask for commands
BASE_COMMAND = '10000001'

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

"""
# noqa: E501
Требует очистку от накипи и вынут модуль для кипятка
[0xd0, 0x12, 0x75, 0x0f, 0x00, 0x04, 0x00, 0x04, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x76, 0x42]

Требует очистку от накипи и всунут модуль для кипятка
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x05, 0x00, 0x04, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x30, 0x54]

Требует очистку от накипи и всунут молочник
[0xd0, 0x12, 0x75, 0x0f, 0x04, 0x05, 0x01, 0x04, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa8, 0xd3]

Требует очистку от накипи и всунут модуль для кипятка и вынут бак с водой
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x15, 0x00, 0x04, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0x04]
То же но очистку от накипи не требует
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x15, 0x00, 0x00, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xaa, 0x31]

Требует очистку от накипи и всунут модуль для кипятка и вынут контейнер для гущи
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x0d, 0x00, 0x04, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2b, 0xfc]
То же но очистку от накипи не требует
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x0d, 0x00, 0x00, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x86, 0xc9]
Для сравнения когда все хорошо
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x05, 0x00, 0x00, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x9d, 0x61]

Требует очистку от накипи и вынут модуль для кипятка и вынут контейнер для гущи
[0xd0, 0x12, 0x75, 0x0f, 0x00, 0x0c, 0x00, 0x04, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x6d, 0xea]

Требует очистку от накипи и всунут молочник и вынут контейнер для гущи
[0xd0, 0x12, 0x75, 0x0f, 0x04, 0x0d, 0x01, 0x04, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xb3, 0x7b]

Требует очистку от накипи и всунут модуль для кипятка и кончилась вода
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x45, 0x00, 0x05, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x82, 0x51]

Требует очистку от накипи выключилась
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x01, 0x00, 0x04, 0x00, 0x00, 0x03, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7b, 0xa3]

Приготовление кофе обычного
Помол
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x05, 0x00, 0x00, 0x00, 0x07, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x5c, 0xa7]
Разогрев кипятка
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x03, 0x00, 0x00, 0x00, 0x07, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x8f, 0x1[0x
Заливка кипятком еще
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x03, 0x00, 0x00, 0x00, 0x07, 0x0b, 0x22, 0x00, 0x00, 0x00, 0x00, 0x00, 0x63, 0x38]
Заливка кипятком чуть осталось
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x03, 0x00, 0x00, 0x00, 0x07, 0x0b, 0x43, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79, 0x80]
Завершение
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x03, 0x00, 0x00, 0x00, 0x07, 0x0d, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x25, 0xec]

нет воды
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x45, 0x00, 0x01, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2f, 0x64]

Переполнен бак
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x05, 0x00, 0x02, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x43, 0xd0]
Чет как-то выключилась
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x41, 0x00, 0x01, 0x00, 0x00, 0x03, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x64, 0x93]

выключена вынут бак нужна очистка
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x11, 0x00, 0x04, 0x00, 0x00, 0x03, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x4c, 0xf3]

выключена все вставлено нужна очистка
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x01, 0x00, 0x04, 0x00, 0x00, 0x03, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7b, 0xa3]

[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x41, 0x00, 0x05, 0x00, 0x00, 0x03, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc9, 0xa6]
[0xd0, 0x12, 0x75, 0x0f, 0x01, 0x05, 0x00, 0x0c, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7a, 0x1f]
"""
