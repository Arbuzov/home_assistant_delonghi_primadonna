## How to Enable Debug Logs
To see the debug information in Home Assistant, you need to configure the `logger` component.

1. Permanent Configuration (Recommended)
Add the following to your `configuration.yaml` file and restart Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.delonghi_primadonna: debug
```
2. Temporary Configuration (No Restart)
You can use the `logger.set_level` service to enable debug logs immediately without restarting:

Go to `Developer Tools` > `Services`.
Select the `logger.set_level` service.
Use the following YAML:
```yaml
custom_components.delonghi_primadonna: debug
```
Click **Call Service**.

## These are debug notes collected from the device

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
|d0 07 a9 f0 04 01 d4 e8|Profile 4 **rejected**|Byte 5 is the status: `00` accepted, `01` rejected. Previously mislabelled as a "Guest" response - that machine refused slot 4.|

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
| 0xa4     | Request profile list (see "Profile list" below)     |
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
| 106 | Maintenance | Total Water Quantity | Divide by 2000 for Liters |
| 108 | Maintenance | Filter Replacements | |
| 111 | Maintenance | Milk Cleaning Count | |
| 3000 | Beverage | Black Coffee Total (Part 1) | Combine with 3077 |
| 3001 | Beverage | Coffee with Milk Total (Part 1) | Combine with 3003 |
| 3003 | Beverage | Coffee with Milk Total (Part 2) | Combined as ID -3003 |
| 3017 | Beverage | Total with Cold Milk | `TOTAL_BEVERAGE_WITH_COLD_MILK` in APK |
| 3021 | Beverage | Total Choco | `TOTAL_CHOCO` in APK |
| 3025 | Beverage | Total Tea | `TOTAL_TEA` in APK |
| 3047 | Beverage | Total "To Go" (Part 1) | Combine with 3048 |
| 3048 | Beverage | Total "To Go" (Part 2) | |
| 3077 | Beverage | Black Coffee Total (Part 2) | Combined as ID -3077 |
| 3078 | Beverage | Total Beverage (Part 2?) | |
| 3080 | Beverage | Total Beverage (Part 1?) | |

**Combined Calculations:**
- **Total Black Coffee**: `ID 3000` + `ID 3077` (Result stored as `-3077`)
- **Total Coffee with Milk**: `ID 3001` + `ID 3003` (Result stored as `-3003`)
- **Total To-Go**: `ID 3047` + `ID 3048`
- **Other Beverage**: `ID 3080` + `ID 3078`

> [!NOTE]
> **The Milk Cleaning ID Discrepancy**
> Analysis of the decompiled APK (`b7.e.java` line 508) shows that the official app requests **ID 115** for the milk cleaning counter. However, some integration users have reported that their machines provide this value on **ID 111**. The current implementation uses 111, but 115 is worth investigating if 111 returns 0.

### Profile list (0xa4)

Captured 2026-08-20 on a machine with six profiles. The exact model was not
recorded, so treat the behavioural notes below as one machine's behaviour
rather than a protocol guarantee; the frame layout itself is confirmed by the
CRCs and by `_parse_profile_response`.

**Observed to be answered only while the machine is awake.** In standby it stayed silent -
not even a status frame comes back - so the request times out. Statistics
(`0xa2`) and settings (`0x95`) *are* answered in standby, which is what
makes the difference easy to miss.

Request, reading a range of profiles (`<start> <end>`, inclusive):

```
0d 07 a4 f0 01 03 d8 2e     profiles 1-3
0d 07 a4 f0 04 06 77 7e     profiles 4-6
```

Response, ~250 ms later:

```
d0 44 a4 f0 00 41 00 6e 00 64 00 72 00 65 00 61 00 00 00 00 00 00 00 00 08
            00 4d 00 61 00 72 00 74 00 69 00 6e 00 00 00 00 00 00 00 00 05
            00 42 00 45 00 33 00 2f 00 42 00 45 00 4e 00 55 00 54 00 5a 03  ed ed
```

Layout: 4 byte header, then one 21-byte record per profile, then 2 byte CRC.
The length byte (`0x44` = 68) is the total frame length minus one.

Each record is 10 characters UTF-16 big-endian, padded with NUL, followed by
one byte:

| Record | Name | Last byte |
|---|---|---|
| 1 | `Andrea` | `0x08` |
| 2 | `Martin` | `0x05` |
| 3 | `BE3/BENUTZ` | `0x03` |
| 4-6 | `BE4/BENUTZ` … | `0x03` |

The last byte is the **icon** shown for that profile. The two personalised
profiles carry different values while all four factory profiles share one,
which rules out a simple "configured" flag. Independently confirmed by
[longshot](https://github.com/mmastrac/longshot), which decodes the same
structure as `WideStringWithIcon { name: String, icon: u8 }` and uses it for
both `ProfileNameRead` and `RecipeNameRead`. The icon values themselves are
not enumerated there.

Names are truncated to the 10 character field: the factory name is
`BE3/BENUTZER`, the machine reports `BE3/BENUTZ`.

The response carries no index, so the reader has to remember which range it
asked for.

The two personalised profile names in the example above were replaced with
placeholders of the same length and the frame's CRC recomputed, so the layout,
the padding and the icon bytes are exactly as captured while the names are not.
The factory names are unchanged.

### Machine state (byte 9 of a 0x75 frame)

Measured 2026-08-20 across a full power cycle, with the percentage in
byte 11 and the stage counter in byte 10:

```
19:31:23   status 07                    ready
           -- power off sent 19:31:30 --
19:31:35   status 02  stage 01          shutting down

           -- power on sent 19:40:43 --
19:40:53   status 01  stage 02    0 %   turning on
19:41:04   status 01  stage 05   54 %
19:41:17   status 01  stage 07  100 %
19:41:29   status 07                    ready
```

So **2 is shutting down, not washing**, and 1 covers the whole warm-up
rather than being a momentary state. Byte 5 alternates between `0x02`
(MotorUp) and `0x04` (MotorDown) during the rinse, resting at `0x04`.

### Beverage start (0x83)

Captured 2026-10-26 on a Maestosa (EPAM960.75.GLM) from an iOS Bluetooth
log of Coffee Link, profile 1. Tag names are
[longshot](https://github.com/mmastrac/longshot)'s
(`src/protocol/hardware_enums.rs`); the meanings marked *observed* were
confirmed on this machine.

```
0d LL 83 f0 <beverage> <trigger> <tag value>... <profile << 2 | mode> <crc crc>
```

`LL` is the total frame length minus one, the CRC is `crc_hqx(frame[:-2],
0x1D0F)` as for every other command. The machine replies `d0 07 83 f0 xx yy
crc crc`; the replies seen are listed with each case below.

**Frames longer than 20 bytes must be split.** The machine's ATT MTU is 23,
and a single write longer than 20 bytes (sent through an ESPHome Bluetooth
proxy) got no reply and started nothing. The app
writes 20 bytes, then the rest, and the machine reassembles the frame from
the length byte. Every coffee-and-milk start is longer than 20 bytes.
`send_command` splits frames the same way since #280.

The app's Espresso Macchiato, 25 bytes:

```
0d 18 83 f0 0b 01 00 02 01 00 4f 02 03 04 00 09 00 52 0b 01 1c 02 06 12 a0
```

| Bytes | Meaning |
|---|---|
| `0b` | beverage: Espresso Macchiato |
| `01` | trigger: start |
| `00 02` | temperature 2 |
| `01 00 4f` | coffee 79 ml |
| `02 03` | strength 3 |
| `04 00` | bean tin 1 |
| `09 00 52` | milk 8.2 s |
| `0b 01` | froth 1 |
| `1c 02` | accessory: milk carafe |
| `06` | profile 1 (`1 << 2`), mode 2: prepare |

Reply `d0 07 83 f0 01 00`, 0.2 s later. About 20 s earlier the app had sent
the same tags with trigger `00` and last byte `05` (profile 1, mode 1: save),
answered `d0 07 83 f0 00 01`: that **saved** them to the profile. A recipe read (`0xa6`) afterwards
returned the app's strength and bean tin, not the ones stored before.

Tags, one byte each except `01`, `09` and `0f`, which are 16-bit big-endian:

| Tag | longshot name | Notes |
|---|---|---|
| `00` | Temp | 0-3 |
| `01` | Coffee | ml |
| `02` | Taste | strength 1-5 (0 = pre-ground) |
| `04` | Blend | *observed*: bean tin on a two-hopper machine, `00` tin 1, `01` tin 2 |
| `08` | DueXPer | `01` on the 2X Espresso |
| `09` | Milk | *observed*: tenths of a second on the Maestosa, not ml |
| `0b` | MilkFroth | 1-3 |
| `0c` | Inversion | milk first |
| `0f` | HotWater | ml |
| `18` | Programmable | recipe metadata, not sent |
| `19` | Visible | recipe metadata, not sent |
| `1b` | IndexLength | recipe metadata, not sent |
| `1c` | Accessorio | `02` milk carafe; the app sends it on milk drinks |

The app sends the tags in ascending order with `1c` last. A short (17-byte,
so not affected by the write limit) macchiato start with the tags in recipe
order and no `1c` was ignored; which of the two the machine needs was not
separated. Coffee-only starts with the tags out of order were accepted.

The trigger and mode names below are Coffee Link's own (Android 4.9.6, which
builds this frame in its `dispenseBeveragePacket`). The last byte is
`(profile << 2) | mode`, so `06` is profile 1 with mode 2, not longshot's
PrepareInversion.

| Trigger | Coffee Link | | Mode | Coffee Link |
|---|---|---|---|---|
| `00` | DONTCARE | | `0` | DELETE_BEVERAGE |
| `01` | START | | `1` | SAVE_BEVERAGE |
| `02` | START_PROGRAM / STOPV2 | | `2` | PREPARE_BEVERAGE |
| `03` | CHECK_START | | `3` | PREPARE_AND_SAVE_BEVERAGE |
| `04` | STOP | | `5` | SAVE_BEVERAGE_INVERSION |
| `05` | STOP_PROGRAM | | `6` | PREPARE_BEVERAGE_INVERSION |
| `06` | SKIP_RINSE | | `7` | PREPARE_SAVE_BEVERAGE_INVERSION |
| `07` | ADVANCED_MODE | | | |

The app sets the top bit of the trigger (`| 0x80`) in one case not traced
here. It only sends tags below `0x17`, plus `1c` and a few newer ones
(`1f` iced, `21` mug adjust, `26` intensity, `27` rinse), so `17` CleanType
is never sent. The stop this integration sends (`83 f0 <beverage> 02 06`) is
STOPV2 for profile 1.

The recipe stored for a beverage (`0d 07 a6 f0 <profile> <beverage> crc
crc`) and its ranges (`0d 06 b0 f0 <beverage> crc crc`, one
`<tag> <min> <default> <max>` group per tag) list which tags a beverage
takes. The app reads both for every beverage when it connects.

**After any milk beverage starts** the machine raises alarm bit 14 (the
`clean_knob` status) and keeps it until the clean prompt on its screen is
answered or the carafe is removed. Coffee-only starts are still accepted
while it is up. A Hot Milk start sent then was accepted but held behind the
prompt, and dropped when the prompt was cancelled. Nothing in the capture
shows the app answering the prompt; it was answered on the machine.
Sent while it was up, trigger `03` (CHECK_START) and `06` (SKIP_RINSE) for
the Macchiato (`83 f0 0b 03 06`, `83 f0 0b 06 06`) were each answered
`d0 07 83 f0 01 01` and left the prompt on screen. Coffee Link has no milk
clean command: nothing in it builds one, and its Maestosa entry in
`assets/MachinesModels.json` lists no cleaning setting.

#### Capturing the app's traffic on iOS

1. Install Apple's Bluetooth logging profile for iOS from
   [Profiles and Logs](https://developer.apple.com/bug-reporting/profiles-and-logs/).
2. Disconnect Home Assistant from the machine (it accepts one connection),
   then use the app.
3. Trigger a sysdiagnose (both volume buttons and the side button briefly),
   wait for it to finish and copy it off the phone.
4. The log is `logs/Bluetooth/bluetoothd-hci-*.pklg` in the archive.
   PacketLogger opens it, or read the ATT writes (`0x12`) and notifications
   (`0x1b`) on CID 4 directly: each record is a 4-byte big-endian length,
   an 8-byte timestamp, a 1-byte type (`02` sent, `03` received) and the HCI
   ACL packet.
