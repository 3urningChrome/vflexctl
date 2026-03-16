# vflexctl

An unofficial CLI (and Python library) for reading and configuring **Werewolf Audio VFlex** USB-C power adapters over their MIDI control interface.

Why? I dunno, I like the idea of being able to work this without needing a website?

---

## Table of Contents

- [Installation](#installation)
- [CLI Usage](#cli-usage)
  - [Reading State](#reading-your-vflex)
  - [Setting Voltage](#voltage)
  - [Setting LED State](#led-state)
  - [Deep Adjust Mode](#--deep-adjust)
  - [Logging / Debug](#logging--debug)
- [Library Usage (The VFlex Object)](#the-vflex-object)
- [Architecture](#architecture)
  - [Package Layout](#package-layout)
  - [Protocol Overview](#protocol-overview)
  - [Data Flow](#data-flow)
  - [Exception Hierarchy](#exception-hierarchy)
- [Development](#development)

---

## Installation

This requires that you have `pipx` installed on your system, using Python 3.12 or later.

Using `pipx`, install this tool with:

```sh
pipx install vflexctl
```

### From Source

```sh
git clone <repo-url>
cd vflexctl
pip install -e .
```

---

## CLI Usage

### Reading your VFlex

To read your VFlex's current state, use the `read` command:

```sh
$ vflexctl read
VFlex Serial Number: <your serial here>
Current Voltage: 12.00
LED State: Always On
```

You can set either your voltage, LED state (always on or not always on), or both:

```sh
vflexctl set -v <voltage> -l <always-on|disabled>
```

### Voltage

Voltage is set with the `--voltage` or `-v` flag, with your volts as XX.XX. For example:

```sh
vflexctl set -v 12
vflexctl set -v 5.50
vflexctl set -v 48.5
vflexctl set -v 12.0000001
```

The VFlex communication over MIDI limits the maximum voltage to around 65.5V
(the limit of a 16-bit unsigned integer = 65 535 mV). Trying to set a higher value
will prevent the voltage from being set.

Internally, the voltage you provide is converted to millivolts (integer), rounded
down to 2 decimal places using `Decimal` to avoid float artefacts, and then
encoded as a big-endian 16-bit value in the protocol.

### LED state

LED state is set using the `--led` or `-l` flag, with the value as either:

```sh
vflexctl set -l always-on    # Factory default -- LED stays lit
vflexctl set -l disabled      # LED turns off during operation
```

To set both voltage and LED state, use both flags (in any order).

### --deep-adjust

`--deep-adjust` is a global flag that forces the old (<= 0.1.2) full-handshake
behaviour before every mutation.

Since 0.2.0, the tool only sends a serial-number request after the initial wake-up
(a *quick handshake*).  This is faster but slightly less thorough.  Add the flag
to force the *full handshake* (serial + voltage + LED re-read) if you'd like
extra certainty:

```sh
vflexctl --deep-adjust set -v 12
```

Open a PR (or an issue) if this doesn't work.

### Logging / Debug

```sh
vflexctl --verbose set -v 12      # INFO-level logs (MIDI sequences, etc.)
vflexctl --debug   set -v 12      # DEBUG-level logs (individual MIDI bytes)
```

---

## The VFlex Object

If you're using this as a library (firstly, yay! welcome!) you have access to the
`VFlex` class:

```python
from vflexctl.device_interface import VFlex
```

### Constructors

| Method | Description |
|--------|-------------|
| `VFlex.get_any(safe_adjust=True, full_handshake=False, wake=False)` | Open the first MIDI port matching the default name *"Werewolf vFlex"*. Used by the CLI. |
| `VFlex.with_io_name(name, *, safe_adjust=True, full_handshake=False, wake=False)` | Open a **specific** MIDI port by its MIDO port name. |

### Key Methods

| Method | Description |
|--------|-------------|
| `initial_wake_up()` | Full handshake: fetch serial number, voltage, LED state, firmware version. Call this before reading state. |
| `get_voltage(update_self=True)` | Query live voltage (millivolts). Returns the value *and* updates `current_voltage` unless `update_self=False`. |
| `set_voltage(millivolts)` | Set the output voltage. Runs a safety guard first (if `safe_adjust` is enabled). |
| `set_voltage_volts(volts)` | Convenience wrapper -- accepts volts as a `float`, converts to millivolts internally. |
| `get_led_state()` | Query LED behaviour. Returns `True` if the LED is *disabled during operation*. |
| `set_led_state(led_state)` | Set LED behaviour. `False` / `0` = always on, `True` / `1` = disabled during operation. |
| `get_serial_number()` | Fetch the 8-character ASCII serial. Raises `SerialNumberMismatchError` if it changes mid-session when `safe_adjust` is enabled. |
| `get_firmware_version()` | Fetch the firmware version string (format `APP.##.##.##`). |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `io_port` | `BaseIOPort` | Underlying MIDO I/O port for direct MIDI access. |
| `serial_number` | `str \| None` | Cached serial number (populated after wake-up). |
| `current_voltage` | `int \| None` | Last known voltage in millivolts. |
| `led_state` | `bool \| None` | `False` = always on, `True` = disabled during operation. |
| `firmware_version` | `str \| None` | Firmware version string. |
| `led_state_str` | `str` | Human-readable LED state (`"always on"` or `"disabled during operation"`). |
| `supports_pdo_scan` | `bool` | `True` if firmware >= `APP.05.00.00`. |

### Safety Mechanism

When `safe_adjust=True` (the default), two guards are active:

1. **Serial-number guard** -- Every handshake re-fetches the serial number. If
   it changes, a `SerialNumberMismatchError` is raised (the physical device may
   have been swapped).
2. **Voltage guard** -- Before `set_voltage`, the current voltage is re-read. If
   it doesn't match the cached value, a `VoltageMismatchError` is raised.

---

## Architecture

### Package Layout

```
src/vflexctl/
├── __init__.py              # Package docstring & metadata
├── cli.py                   # Typer sub-commands (read, set)
├── main.py                  # Entry-point, global options, logging config
├── context.py               # Pydantic AppContext (carries --deep-adjust flag)
├── types.py                 # Shared type aliases (MIDITriplet, VFlexProtoMessage)
├── exceptions.py            # Custom exception hierarchy
├── py.typed                 # PEP 561 marker
│
├── protocol/                # ── Low-level protocol layer ──
│   ├── __init__.py          # Re-exports VFlexProto, framing helpers
│   ├── protocol.py          # VFlexProto constants, MIDI↔protocol conversion
│   ├── command_framing.py   # Prepend length byte, wrap in START/END sentinels
│   ├── logger.py            # Shared structlog logger for the protocol package
│   └── coders/              # Payload encoders / decoders
│       ├── __init__.py      # Re-exports all coders
│       ├── voltage.py       # 16-bit millivolt encode/decode
│       ├── led_state.py     # Single-byte LED state decode
│       └── hardware_info.py # ASCII serial, firmware version, hw revision
│
├── command/                 # ── Command builders ──
│   ├── __init__.py          # Re-exports public command functions
│   ├── voltage.py           # set_voltage_command, get_voltage_command
│   ├── led.py               # set_led_state_command
│   └── hardware_info.py     # get_firmware_version_command, get_hardware_revision_command
│
├── device_interface/        # ── High-level device API ──
│   ├── __init__.py          # Re-exports VFlex
│   ├── vflex.py             # VFlex class + run_with_handshake decorator
│   └── common_sequences.py  # Pre-built MIDI sequences for read-only queries
│
├── midi_transport/          # ── MIDI I/O helpers ──
│   ├── receivers.py         # drain_incoming, drain_once
│   └── senders.py           # send_sequence, send_triplet
│
└── input_handler/           # ── User-input normalisation ──
    └── voltage_convert.py   # voltage_to_millivolt, decimal_normalise_voltage
```

### Protocol Overview

The VFlex adapter communicates via a custom protocol layered on top of
standard **MIDI NOTE_ON** messages.  Each protocol byte is split into two
4-bit nibbles and encoded in the *note* and *velocity* fields of a NOTE_ON
event (status byte `0x90`).

A single protocol frame on the wire looks like:

```
┌─────────────┬───────────────────────────────────────────┬───────────────┐
│ START       │ Protocol bytes (nibble-encoded as NOTE_ON)│ END           │
│ (0x80,0,0)  │ [length] [cmd] [payload …]                │ (0xA0,0,0)    │
└─────────────┴───────────────────────────────────────────┴───────────────┘
```

- **`length`** (byte 0) -- total count of protocol bytes (inclusive).
- **`cmd`** (byte 1) -- command identifier (e.g. `0x12` = get/set voltage).
- **payload** -- zero or more bytes whose meaning depends on the command.

**Known command bytes:**

| Byte   | Name                        | Payload                            |
|--------|-----------------------------|------------------------------------|
| `0x08` | `CMD_GET_SERIAL_NUMBER`     | → 8 ASCII chars                    |
| `0x0A` | `CMD_GET_HARDWARE_REVISION` | → variable ASCII                   |
| `0x0B` | `CMD_GET_FIRMWARE_VERSION`  | → 12 ASCII chars (`APP.##.##.##`)  |
| `0x0F` | `CMD_GET_LED_STATE`         | → 1 byte (0 or 1)                  |
| `0x8F` | `CMD_SET_LED_STATE`         | 1 byte →                           |
| `0x12` | `CMD_GET_VOLTAGE`           | → 2 bytes (big-endian mV)          |
| `0x92` | `CMD_SET_VOLTAGE`           | 2 bytes (big-endian mV) →          |

SET commands have the high bit (`0x80`) OR'd onto the corresponding GET
command byte.

### Data Flow

A typical **set voltage** operation flows through the layers as follows:

```
CLI (cli.py)
  │  user passes -v 12.0
  ▼
input_handler/voltage_convert.py
  │  12.0  →  12000 mV (int)
  ▼
command/voltage.py
  │  set_voltage_command(12000)  →  [0x92, high, low]
  ▼
protocol/command_framing.py
  │  prepare_command_frame(...)  →  [4, 0x92, high, low]
  │  prepare_command_for_sending(...)  →  [(0x80,0,0), ..., (0xA0,0,0)]
  ▼
midi_transport/senders.py
  │  send_sequence(port, midi_triplets)
  ▼
  ═══  MIDI wire  ═══
  ▼
midi_transport/receivers.py
  │  drain_incoming(port)  →  list[MIDITriplet]
  ▼
protocol/protocol.py
  │  protocol_message_from_midi_messages(...)  →  [4, 0x12, hi, lo]
  ▼
protocol/coders/voltage.py
  │  get_millivolts_from_protocol_message(...)  →  12000
  ▼
device_interface/vflex.py
  │  v_flex.current_voltage = 12000
```

### Exception Hierarchy

```
ValueError
└── InvalidProtocolMessageError        # Malformed protocol message
    ├── InvalidProtocolMessageLengthError   # Wrong byte count
    └── IncorrectCommandByte               # Unexpected command ID

Exception
└── UnsafeAdjustmentError              # Safety check failed
    ├── SerialNumberMismatchError      # Device serial changed mid-session
    └── VoltageMismatchError           # Cached vs. live voltage mismatch
```

---

## Development

This project uses poetry for managing dependencies and building, built with Python 3.12.10. Unless there's
a huge shift and poetry becomes terrible, please don't commit in a requirements.txt.

There are `black` rules for formatting in pyproject.toml as well - if your IDE formats on save, it (should)
pick these up and format your files for you. The project also uses `mypy` for typing. Since this has a `py.typed`,
you likely want to run `mypy .` and fix any typing issues before opening a PR or something.

### Running Tests

```sh
pytest test/ -v
```

### Type Checking

```sh
mypy src/
```

### Formatting

```sh
black src/ test/
```

Fork/pull/PR as you want!

---

This is an independent hobby project.
It is not affiliated with, endorsed by, or connected to any company.
All product names, trademarks, and brands are the property of their respective owners.

## License

Apache 2.0 -- see [LICENSE](LICENSE) for details.
