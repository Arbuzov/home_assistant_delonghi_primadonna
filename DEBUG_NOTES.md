## This is a debug notes collected from the device

Please join

|Code                                                    | Details                            |
|--------------------------------------------------------|------------------------------------|
|d0 12 75 0f 01 05 00 00 00 07 00 00 00 00 00 00 00 9d 61|All is good                         |
|d0 12 75 0f 01 15 00 00 00 07 00 00 00 00 00 00 00 aa 31|No water tank                       |
|d0 12 75 0f 01 0d 00 00 00 07 00 00 00 00 00 00 00 86 c9|No recycle tank                     |
|d0 12 75 0f 01 01 00 00 00 00 03 00 00 00 00 00 00 8f 2f|Power off                           |
|d0 12 75 0f 01 01 00 00 00 00 03 64 00 00 00 00 00 d6 96|Power off                           |
|d0 12 75 0f 01 01 00 00 00 01 07 64 00 00 00 00 00 50 83|Turning on                          |
|d0 12 75 0f 01 45 00 01 00 07 00 00 00 00 00 00 00 2f 64|Requested fresh water               |
|d0 12 75 0f 01 03 00 00 00 01 05 08 00 00 00 00 00 62 71|Washing I suppose                   |
|d0 12 75 0f 01 01 00 00 00 01 01 00 00 00 00 00 00 a8 1f|Heat water                          |
|d0 12 75 0f 01 03 00 00 00 01 05 61 00 00 00 00 00 75 8b|Device is ready notification        |
|d0 12 75 0f 01 01 00 04 00 00 03 64 00 00 00 00 00 7b a3|Power off device asks for cleanup   |

|Codes for Dinamica Plus                                 | Details                            |Notification|
|--------------------------------------------------------|------------------------------------|------------|
|**Sequences**|||
|d0 12 75 0f 02 00 01 00 00 01 01 00 00 00 00 00 00 bc 86|Sequence 1 - Powered on             ||
|d0 12 75 0f 02 02 01 00 00 01 05 1d 00 00 00 00 00 2f 6d|Sequence 2 - Unknown?               ||
|d0 12 75 0f 02 00 01 00 00 01 07 64 00 00 00 00 00 44 1a|Sequence 3 - Unknown?               ||
|d0 12 75 0f 02 04 01 00 00 07 00 00 00 00 00 00 00 89 f8|Sequence 4 - Ready (`Milk Carafe` is in the `Frothing` position)||
|d0 12 75 0f 02 00 01 00 00 00 03 64 00 00 00 00 00 c2 0f|Sequence 5 - Power off              ||
|**Cleaning**|||
|d0 12 75 0f 04 05 01 00 40 0c 03 0d 00 00 00 00 00 1a 51|Started cleaning `Milk Carafe` spout (nozzle in `Clean` position)||
|d0 12 75 0f 04 05 01 00 00 07 00 00 00 00 00 00 00 05 e6|Finished cleaning `Milk Carafe` spout (nozzle in `Clean` position)||
|d0 12 75 0f 02 00 01 00 00 08 02 00 00 00 00 00 00 3d 0d|Started `rinsing` machine||
|d0 12 75 0f 02 02 01 00 00 08 05 43 00 00 00 00 00 86 53|Finished `rinsing` machine - Unknown?||
|**Insert / Remove**|||
|                                                        |Inserted `Water Tank`               |DeviceOK|
|d0 12 75 0f 01 15 00 00 00 01 00 00 00 00 00 00 00 2a fa|Removed `Water Tank`                |NoWaterTank|
|                                                        |Inserted `Hot Water Nozzle`         ||
|d0 12 75 0f 00 04 00 00 00 07 00 00 00 00 00 00 00 db 77|Removed `Hot Water Nozzle`          ||
|**Beverages**|||
|d0 12 75 0f 01 05 00 00 00 0b 03 07 00 00 00 00 00 9c 15|Started `Hot Water` beverage        ||
|d0 12 75 0f 02 04 01 00 00 0a 02 00 00 00 00 00 00 bf 7f|Starting `Latte Machiato` beverage?||
|d0 12 75 0f 02 00 01 00 40 07 0e 64 00 00 00 00 00 b0 c4|Finished / cancelled `unknown` beverage?||
|**Profiles**|||
|d0 07 a9 f0 01 00 3b 3c|Set Profile 1 response||
|d0 07 a9 f0 02 00 6e 6f|Set Profile 2 response||
|d0 07 a9 f0 03 00 5d 5e|Set Profile 3 response||
|d0 07 a9 f0 04 01 d4 e8|Set Profile Guest response||

### Management protocol

### The commands have a request and response id

The request id is the third byte of the command, the response id must be the same as request id.
|Request ID|Purpose                                              |
|----------|-----------------------------------------------------|
| 0x75     | Device status                                       |
| 0x83     | Prepare or manage beverage                          |
| 0x84     | Power on command                                    |
| 0x90     | Manage device settings                              |
| 0x95     |                                                     |
| 0xa2     | Statistics request/response                         |
| 0xa3     |                                                     |
| 0xa4     | Request profile list                                |
| 0xa5     |                                                     |
| 0xa9     | Switch the user profile                             |
| 0xaa     |                                                     |
| 0xd2     |                                                     |

Switches managed by command [0x0d, 0x0b, 0x90, 0x0f, 0x00, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
The nine digit (counted from 0) is the command bitmask

### Notification Protocol assumptions
|Code    | Details                                             |
|--------|-----------------------------------------------------|
|00 - 03 | was not changed suspect pilot or device type
|04      | nozzle sensor hot water, milk pot or detached
|05      | General notification bitmask is suspected
|        | 0
|        | 1
|        | 2
|        | 3
|        | 4
|        | 5
|        | 6
|        | 7
|06      | Ability to use milk pot, maybe
|07      | Service notification bitmask is suspected
|        | 0
|        | 1
|        | 2 - descale
|        | 3 - replace water filter
|        | 4
|        | 5
|        | 6
|        | 7
|08      | always 0
|09      | 0x00 if device active 0x07 if device is off
|10      | cooking progress stage
|11      | progress bar inside the stage
|12 - 16 | always 0 perhaps for the new features
|17 - 18 | Signature
|99      | Always 0

### Statistics Protocol (0xA2)

This command is used to request various counters (beverages, maintenance, etc.) from the machine.

#### Request Format
`[0x0D, 0x08, 0xA2, 0x0F, ID_HI, ID_LO, COUNT, CRC_HI, CRC_LO]`
- `ID_HI/LO`: Starting parameter ID (e.g., `0x00 0x64` for ID 100).
- `COUNT`: Number of parameters to return.

#### Response Format
`[0xD0, LEN, 0xA2, 0x0F, ID_HI, ID_LO, VAL_B3, VAL_B2, VAL_B1, VAL_B0, ...]`
- **Implicit ID**: The first 4 bytes of value (`VAL_B3..B0`) belong to the ID requested in bytes 4-5.
- **Explicit ID**: Subsequent values are formatted as `[ID_HI, ID_LO, VAL_B3, VAL_B2, VAL_B1, VAL_B0]`.

**NOTE**: All multi-byte values (IDs and Counters) are **Big Endian**.
- `ID_HI` is the most significant byte.
- `VAL_B3` is the most significant byte of the 32-bit integer value.

> [!WARNING]
> **Decoding Bug**: Ensure you skip the bytes 4-5 when reading the first value. If you read from byte 4 as a 4-byte integer, you will get a value like `196673536` for ID 3000 (which is `0x0B B8 << 16`).

#### Parameter ID Map

| ID | Category | Description | Notes |
|----|----------|-------------|-------|
| 105 | Maintenance | Descaling Count | |
| 106 | Maintenance | Total Water Quantity | Divide by 2000 (or 5000) for Liters |
| 108 | Maintenance | Filter Replacements | |
| 115 | Maintenance | Milk Cleaning Count | |
| 3000 | Beverage | Black Coffee Total (Part 1) | Combine with 3077 |
| 3001 | Beverage | Coffee with Milk Total (Part 1) | Combine with 3003 |
| 3003 | Beverage | Coffee with Milk Total (Part 2) | |
| 3017 | Beverage | Additional Coffee | |
| 3021 | Beverage | Total Choco | |
| 3025 | Beverage | Total Tea | |
| 3047 | Beverage | Total "To Go" (Part 1) | Combine with 3048 |
| 3048 | Beverage | Total "To Go" (Part 2) | |
| 3077 | Beverage | Black Coffee Total (Part 2) | |
| 3078 | Beverage | Total Beverage (Part 2?) | |
| 3080 | Beverage | Total Beverage (Part 1?) | |

**Combined Calculations:**
- **Total Black Coffee**: `ID 3000` + `ID 3077`
- **Total Coffee with Milk**: `ID 3001` + `ID 3003`
- **Total To-Go**: `ID 3047` + `ID 3048`
- **Other Beverage**: `ID 3080` + `ID 3078`