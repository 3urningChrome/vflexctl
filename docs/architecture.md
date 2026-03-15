# Architecture

This document describes the internal architecture of **vflexctl**: how the modules are laid out, what each layer is responsible for, and how data flows from a CLI command down to raw MIDI bytes on the wire.

---

## Module Hierarchy

```
vflexctl/
├── main.py                          (1) Entry-point & global logging
├── cli.py                           (2) Typer CLI commands
├── types.py                         shared type aliases
├── exceptions.py                    custom exception hierarchy
│
├── device_interface/
│   ├── vflex.py                     (3) High-level VFlex device API
│   └── common_sequences.py          (4) Pre-built read sequences
│
├── protocol/
│   ├── protocol.py                  (5) Protocol constants & MIDI↔protocol codec
│   ├── command_framing.py           (6) Frame builder & MIDI byte serialiser
│   ├── logger.py                    shared protocol logger
│   └── coders/
│       ├── voltage.py               (7) Voltage encode / decode
│       ├── led_state.py             (7) LED-state decode
│       └── serial_number.py         (7) Serial-number decode
│
├── command/
│   ├── voltage.py                   (8) Voltage command builders
│   └── led.py                       (8) LED command builder
│
├── input_handler/
│   └── voltage_convert.py           (9) Volt → millivolt conversion
│
└── midi_transport/
    ├── senders.py                   (10) Low-level MIDI send
    └── receivers.py                 (10) Low-level MIDI receive/drain
```

The numbers in parentheses correspond to the layers described below.

---

## Layers

### (1) Entry-point — `main.py`

`main.py` owns the application bootstrap.

- Registers the `--verbose` / `--debug` global flags on the Typer `cli` application.
- Calls `structlog.configure()` to set the minimum log level before any command body runs.
- Exposes `cli` as the `[project.scripts]` entry-point (`vflexctl = "vflexctl.main:cli"`).

### (2) CLI commands — `cli.py`

Thin presentation layer built with [Typer](https://typer.tiangolo.com/) and [Rich](https://github.com/Textualize/rich).

- Defines two commands:
  - `vflexctl read` — prints the current serial, voltage, and LED state.
  - `vflexctl set` — validates input, then delegates to the device interface layer.
- Input validation at this layer:
  - Voltage must be `> 0` and `≤ 65.535` V (MIDI integer ceiling).
  - At least one of `--voltage` / `--led` must be supplied.
- `LEDOption` is a `StrEnum` that maps CLI flag values (`"always-on"`, `"disabled"`) to the boolean values expected by the device interface.

### (3) High-level device API — `device_interface/vflex.py`

The `VFlex` class is the single object that consumers interact with. It hides all protocol framing and MIDI transport behind a clean, method-oriented interface.

Key responsibilities:

| Method | Description |
|---|---|
| `VFlex.get_any()` | Opens the default port (`"Werewolf vFlex"`) |
| `VFlex.with_io_name(name)` | Opens a specific named MIDI port |
| `wake_up()` | Runs the three-step init sequence: serial → LED → voltage |
| `get_serial_number()` | Fetches (or re-fetches) the device serial number |
| `get_voltage()` | Fetches the current output voltage in millivolts |
| `get_led_state()` | Fetches the current LED behaviour flag |
| `set_voltage(millivolts)` | Sends a set-voltage command and confirms the new value |
| `set_voltage_volts(volts)` | Convenience wrapper that converts volts → millivolts |
| `set_led_state(state)` | Sends a set-LED command and re-reads the new state |

#### `run_with_handshake` decorator

The private decorator `run_with_handshake` wraps `get_voltage`, `get_led_state`, `set_voltage`, `set_led_state`, and `_guard_voltage`. It calls `wake_up()` automatically before the wrapped function runs, ensuring the device is initialised.

#### Safe-adjust mode

When `safe_adjust=True` (the default):

- `get_serial_number()` raises `SerialNumberMismatchError` if the serial returned by the device differs from the cached value — preventing modifications to an unexpectedly swapped device.
- `_guard_voltage()` raises `VoltageMismatchError` if the live voltage reading doesn't match the cached `current_voltage` before a `set_voltage()` call.

### (4) Pre-built sequences — `device_interface/common_sequences.py`

Module-level constants that pre-compute the full MIDI byte sequences for the three read commands. Computing these once at import time avoids repeated framing work.

### (5) Protocol constants & codec — `protocol/protocol.py`

`VFlexProto` is a namespace class (no instances) that collects all protocol constants:

| Constant | Value | Meaning |
|---|---|---|
| `COMMAND_START` | `(0x80, 0, 0)` | Start-of-frame sentinel |
| `COMMAND_END` | `(0xA0, 0, 0)` | End-of-frame sentinel |
| `NOTE_STATUS` | `0x90` | MIDI note-on status byte used for data messages |
| `MIDI_CLOCK_HEARTBEAT` | `(0xF8,)` | MIDI clock tick (sent by the vendor app every ~6 s) |
| `CMD_GET_SERIAL_NUMBER` | `0x08` | Get-serial command byte |
| `CMD_GET_LED_STATE` | `0x0F` | Get-LED command byte |
| `CMD_SET_LED_STATE` | `0x8F` | Set-LED command byte (`CMD_GET_LED_STATE \| 0x80`) |
| `CMD_GET_VOLTAGE` | `0x12` | Get-voltage command byte |
| `CMD_SET_VOLTAGE` | `0x92` | Set-voltage command byte (`CMD_GET_VOLTAGE \| 0x80`) |

Also contains:

- `protocol_byte_from_midi_bytes()` — reconstructs one protocol byte from a MIDI triplet by treating MIDI bytes 2 and 3 as high/low nibbles.
- `protocol_message_from_midi_messages()` — decodes a full list of MIDI triplets into a protocol message, stripping the start/end sentinel frames.
- `validate_and_trim_protocol_message()` — validates the self-describing length field and truncates to the declared length.

### (6) Frame builder — `protocol/command_framing.py`

- `prepare_command_frame(sub_command)` — prepends the length byte to a sub-command list.
- `midi_bytes_from_protocol_byte(byte)` — maps one protocol byte to a MIDI triplet by splitting it into high/low nibbles.
- `prepare_command_for_sending(frames)` — wraps one or more frames in `COMMAND_START … COMMAND_END` and converts every protocol byte to its MIDI triplet.

### (7) Coders — `protocol/coders/`

Pure-function encode/decode helpers for each data type:

| Module | Functions |
|---|---|
| `voltage.py` | `protocol_encode_millivolts`, `protocol_decode_millivolts`, `get_millivolts_from_protocol_message` |
| `led_state.py` | `protocol_decode_led_state` |
| `serial_number.py` | `protocol_decode_serial_number` |

### (8) Command builders — `command/`

Create the raw protocol byte-list for each command before framing:

| Function | Protocol bytes |
|---|---|
| `set_voltage_command(millivolts)` | `[CMD_SET_VOLTAGE, high_byte, low_byte]` |
| `get_voltage_command()` | `[CMD_GET_VOLTAGE]` |
| `set_led_state_command(value)` | `[CMD_SET_LED_STATE, int(value)]` |

### (9) Input handler — `input_handler/voltage_convert.py`

Normalises user-supplied voltage values before they reach the device layer:

- `decimal_normalise_voltage(voltage)` — converts any `float`, `int`, or numeric `str` to a `Decimal` rounded down to 2 decimal places.
- `voltage_to_millivolt(voltage)` — returns the integer millivolts representation.

Using `decimal.Decimal` avoids floating-point rounding artefacts (e.g. `5.5 * 1000 == 5499.999...`).

### (10) MIDI transport — `midi_transport/`

Thin wrappers over [mido](https://mido.readthedocs.io/):

- `senders.send_triplet(output, triplet, *, pause)` — sends a single 3-byte MIDI message and sleeps for `pause` seconds (default 2 ms).
- `senders.send_sequence(output, sequence)` — iterates a list of triplets and calls `send_triplet` for each.
- `receivers.drain_once(input_port)` — consumes all currently pending MIDI messages from the port.
- `receivers.drain_incoming(input_port, *, seconds)` — calls `drain_once` in a loop for `seconds` seconds (default 0.5 s), collecting all messages that arrive within the window.

The 2 ms inter-message pause in `send_triplet` and the 0.5 s drain window are empirically chosen timing constants that match the device's observed response latency.

---

## Data Flow

### `vflexctl set -v 12 -l always-on`

```
User
  │
  ▼
cli.py: set_v_flex_state(voltage=12.0, led=LEDOption.ALWAYS_ON)
  │   validate input (0 < 12.0 ≤ 65.535 ✓)
  │
  ▼
device_interface/vflex.py: VFlex.get_any()
  │   → mido.open_ioport("Werewolf vFlex")
  │
  ▼
vflex.wake_up()
  │   → get_serial_number()  ─┐
  │   → _initial_get_led_state() ├─ send_sequence + drain_incoming
  │   → _initial_get_voltage() ─┘
  │
  ▼
vflex.set_voltage_volts(12.0)
  │   → input_handler: voltage_to_millivolt(12.0) → 12000 mV
  │   → vflex.set_voltage(12000)
  │       → run_with_handshake: wake_up()  [second wake-up]
  │       → _guard_voltage()              [safe-adjust check]
  │       → command/voltage: set_voltage_command(12000)
  │           → protocol/coders: protocol_encode_millivolts(12000)
  │               → high=0x2E, low=0xE0
  │           → [CMD_SET_VOLTAGE, 0x2E, 0xE0]
  │       → protocol: prepare_command_frame([...])
  │           → [4, CMD_SET_VOLTAGE, 0x2E, 0xE0]
  │       → protocol: prepare_command_for_sending([...])
  │           → [(0x80,0,0), (0x90,0,4), (0x90,9,2), (0x90,2,14), (0x90,14,0), (0xA0,0,0)]
  │       → midi_transport/senders: send_sequence(port, [...])
  │       → midi_transport/receivers: drain_incoming(port)
  │       → protocol: protocol_message_from_midi_messages(response)
  │       → protocol/coders: get_millivolts_from_protocol_message(msg)
  │       → self.current_voltage = returned_millivolts
  │
  ▼
vflex.set_led_state(False)  [always-on = False]
  │   → run_with_handshake: wake_up()
  │   → command/led: set_led_state_command(False) → [CMD_SET_LED_STATE, 0]
  │   → frame → send → drain
  │   → send GET_LED_STATE_SEQUENCE → drain → decode → self.led_state = False
  │
  ▼
cli.py: print state
```

---

## Dependency Graph

```
main.py
  └── cli.py
        └── device_interface/vflex.py
              ├── command/voltage.py
              │     └── protocol/coders/voltage.py
              ├── command/led.py
              ├── device_interface/common_sequences.py
              │     └── protocol/  (protocol.py, command_framing.py)
              ├── protocol/
              │     ├── protocol.py
              │     ├── command_framing.py
              │     └── coders/
              ├── input_handler/voltage_convert.py
              ├── midi_transport/senders.py
              └── midi_transport/receivers.py
```

External runtime dependencies:

| Package | Role |
|---|---|
| `mido` | MIDI I/O abstraction |
| `python-rtmidi` | Native MIDI backend used by mido |
| `typer` | CLI framework |
| `rich` | Terminal output formatting |
| `colorama` | Cross-platform ANSI colour support |
| `structlog` | Structured logging |
