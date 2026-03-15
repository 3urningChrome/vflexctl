# API Reference

Complete reference for every public module, class, function, and exception in **vflexctl**.

---

## `vflexctl.types`

Shared type aliases used throughout the package.

```python
type MIDITriplet = tuple[int, int, int]
```

A 3-byte MIDI message represented as a tuple of integers.

```python
type VFlexProtoMessage = list[int]
```

A list of integers representing a single VFlex protocol message (before MIDI encoding).

---

## `vflexctl.exceptions`

### Exception Hierarchy

```
Exception
└── UnsafeAdjustmentError
    ├── SerialNumberMismatchError
    └── VoltageMismatchError

ValueError
└── InvalidProtocolMessageError
    └── InvalidProtocolMessageLengthError

InvalidProtocolMessageError
└── IncorrectCommandByte
```

---

### `InvalidProtocolMessageError(ValueError)`

Raised when a received protocol message is structurally invalid.

```python
InvalidProtocolMessageError(
    protocol_message: list[int],
    message: str = "Invalid protocol message"
)
```

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `protocol_message` | `list[int]` | The raw message bytes that triggered the error |

---

### `InvalidProtocolMessageLengthError(InvalidProtocolMessageError)`

Raised when the protocol message has an unexpected number of bytes.

```python
InvalidProtocolMessageLengthError(
    protocol_message: list[int],
    expected_length: int
)
```

The error message is automatically formatted as:
`"Expected {expected_length} bytes but got {len(protocol_message)}"`

---

### `IncorrectCommandByte(InvalidProtocolMessageError)`

Raised when the command byte at position 1 of a protocol message does not match the expected command.

```python
IncorrectCommandByte(
    protocol_message: list[int],
    expected_command: int
)
```

---

### `UnsafeAdjustmentError(Exception)`

Base class for errors raised when a mutating operation would be unsafe.

```python
UnsafeAdjustmentError(ex_message: str | None = None)
```

---

### `SerialNumberMismatchError(UnsafeAdjustmentError)`

Raised when the serial number returned by the device does not match the cached serial number. This indicates that the device may have been swapped between operations.

```python
SerialNumberMismatchError(
    old_serial_number: str | None = None,
    new_serial_number: str | None = None
)
```

---

### `VoltageMismatchError(UnsafeAdjustmentError)`

Raised when the live voltage read from the device does not match the voltage cached on the `VFlex` object. This guard fires before a `set_voltage` call to prevent an unexpected adjustment.

```python
VoltageMismatchError(
    stored_voltage: int | None = None,
    retrieved_voltage: int | None = None
)
```

**Attributes:**

| Attribute | Type | Description |
|---|---|---|
| `stored_voltage` | `int \| None` | The cached millivolt value |
| `retrieved_voltage` | `int \| None` | The live millivolt value read from the device |

---

## `vflexctl.device_interface`

### `VFlex`

High-level interface for communicating with a connected VFlex power adapter.

```python
class VFlex:
    io_port: BaseIOPort
    log: structlog.BoundLogger
    serial_number: str | None
    current_voltage: int | None
    led_state: bool | None
    safe_adjust: bool
```

#### Constructor

```python
VFlex(io_port: BaseIOPort, safe_adjust: bool = True)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `io_port` | `BaseIOPort` | — | An open mido bidirectional I/O port |
| `safe_adjust` | `bool` | `True` | Enable serial-number and voltage guard checks |

#### Class Methods

##### `VFlex.get_any() -> VFlex`

Opens the first available port whose name matches `"Werewolf vFlex"`. If multiple VFLEX devices are connected, the selected device is non-deterministic.

Raises `RuntimeError` if the port is not found.

##### `VFlex.with_io_name(name: str, *, safe_adjust: bool = True) -> VFlex`

Opens the MIDI I/O port with the exact name `name`.

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | The MIDI port name as returned by `mido.get_ioport_names()` |
| `safe_adjust` | `bool` | Enable safety guards (default `True`) |

Raises `RuntimeError` if the port name is not found.

#### Instance Methods

##### `wake_up() -> None`

Runs the initialisation sequence required before any command:

1. `get_serial_number()` — caches the serial number.
2. `_initial_get_led_state()` — caches the LED state.
3. `_initial_get_voltage()` — caches the current voltage.

Methods decorated with `@run_with_handshake` call `wake_up()` automatically.

---

##### `get_serial_number() -> str | None`

Fetches the device serial number via the `GET_SERIAL_NUMBER` command and stores it in `self.serial_number`.

If `safe_adjust` is `True` and the returned serial number differs from the previously cached value, raises `SerialNumberMismatchError`.

Returns `None` (and logs the exception) if decoding fails and `safe_adjust` is `False`.

---

##### `get_voltage(*, update_self: bool = True) -> int`

*Decorated with `@run_with_handshake`.*

Sends the `GET_VOLTAGE` command and returns the current output voltage in millivolts.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `update_self` | `bool` | `True` | Whether to update `self.current_voltage` with the result |

Returns: `int` — millivolts.

---

##### `get_led_state() -> bool`

*Decorated with `@run_with_handshake`.*

Sends the `GET_LED_STATE` command and returns the current LED behaviour flag. Updates `self.led_state`.

Returns: `bool` — `False` for always-on (default), `True` for disabled during operation.

---

##### `set_voltage(millivolts: int) -> None`

*Decorated with `@run_with_handshake`.*

Sets the output voltage to `millivolts`. Calls `_guard_voltage()` first to verify the cached voltage matches the live reading (when `safe_adjust=True`). Updates `self.current_voltage` with the value confirmed by the device after the command.

| Parameter | Type | Description |
|---|---|---|
| `millivolts` | `int` | Desired voltage in millivolts |

Raises `VoltageMismatchError` (via `_guard_voltage`) if the live voltage differs from the cached value.

---

##### `set_voltage_volts(volts: float) -> None`

Convenience wrapper around `set_voltage`. Converts `volts` to millivolts using `voltage_to_millivolt()` before calling `set_voltage()`.

| Parameter | Type | Description |
|---|---|---|
| `volts` | `float` | Desired voltage in volts |

---

##### `set_led_state(led_state: bool | Literal[0, 1]) -> None`

*Decorated with `@run_with_handshake`.*

Sends the `SET_LED_STATE` command, drains the (empty) response, then reads back the state with `GET_LED_STATE` to confirm. Updates `self.led_state`.

| Parameter | Type | Description |
|---|---|---|
| `led_state` | `bool \| Literal[0, 1]` | `False`/`0` = always-on; `True`/`1` = disabled |

---

##### `led_state_str -> str` *(property)*

Returns `"always on"` when `self.led_state is False`, otherwise `"disabled during operation"`.

---

##### `_guard_voltage() -> None`

*Decorated with `@run_with_handshake`.*

Internal safe-adjust guard. Re-reads the voltage from the device and raises `VoltageMismatchError` if it differs from `self.current_voltage`. No-op when `safe_adjust=False`.

---

## `vflexctl.protocol`

### `VFlexProto`

Namespace class (do not instantiate) holding all protocol constants.

| Constant | Type | Value | Description |
|---|---|---|---|
| `COMMAND_START` | `MIDITriplet` | `(0x80, 0, 0)` | Start-of-frame sentinel |
| `COMMAND_END` | `MIDITriplet` | `(0xA0, 0, 0)` | End-of-frame sentinel |
| `NOTE_STATUS` | `int` | `0x90` | MIDI Note-On status byte used for data messages |
| `MIDI_CLOCK_HEARTBEAT` | `tuple` | `(0xF8,)` | MIDI Clock heartbeat (sent by vendor app) |
| `CMD_GET_SERIAL_NUMBER` | `int` | `0x08` | Get-serial command byte |
| `CMD_GET_LED_STATE` | `int` | `0x0F` | Get-LED command byte |
| `CMD_SET_LED_STATE` | `int` | `0x8F` | Set-LED command byte |
| `CMD_GET_VOLTAGE` | `int` | `0x12` | Get-voltage command byte |
| `CMD_SET_VOLTAGE` | `int` | `0x92` | Set-voltage command byte |

---

### `protocol_message_from_midi_messages`

```python
def protocol_message_from_midi_messages(
    midi_messages: list[MIDITriplet]
) -> list[int]
```

Decodes a list of received MIDI triplets into a protocol message.

1. Filters out start/end sentinels.
2. Converts each remaining triplet to a protocol byte via `protocol_byte_from_midi_bytes`.
3. Calls `validate_and_trim_protocol_message` to check the self-described length and trim.

Raises `ValueError` if the message is too short. Raises `IndexError` if the list is empty.

---

### `validate_and_trim_protocol_message`

```python
def validate_and_trim_protocol_message(
    protocol_message: list[int]
) -> list[int]
```

Reads `protocol_message[0]` as the expected total length. Returns `protocol_message[:length]`. Raises `ValueError` if `len(protocol_message) < length`.

---

### `prepare_command_frame`

```python
def prepare_command_frame(
    sub_command: Iterable[int]
) -> list[int]
```

Prepends the length byte to a sub-command. The length counts itself plus the sub-command bytes. Raises `TypeError` if `sub_command` is a `set` (unordered, unsafe for device commands).

Example:

```python
prepare_command_frame([VFlexProto.CMD_GET_VOLTAGE])
# → [2, 0x12]

prepare_command_frame([VFlexProto.CMD_SET_VOLTAGE, 0x2E, 0xE0])
# → [4, 0x92, 0x2E, 0xE0]
```

---

### `prepare_command_for_sending`

```python
def prepare_command_for_sending(
    frames: list[VFlexProtoMessage] | VFlexProtoMessage
) -> list[MIDITriplet]
```

Converts one frame (or a list of frames) into the final list of MIDI triplets ready to be sent to the device.

- Wraps the output in `COMMAND_START … COMMAND_END`.
- Converts each protocol byte to its MIDI triplet using `midi_bytes_from_protocol_byte`.

Raises `ValueError` if `frames` is empty.

---

## `vflexctl.protocol.coders`

### Voltage coders — `vflexctl.protocol.coders.voltage`

#### `protocol_encode_millivolts`

```python
def protocol_encode_millivolts(value: int) -> tuple[int, int]
```

Splits `value` into `(high_byte, low_byte)` for inclusion in a protocol message.

```python
protocol_encode_millivolts(12000)
# → (46, 224)  i.e. (0x2E, 0xE0)
```

#### `protocol_decode_millivolts`

```python
def protocol_decode_millivolts(high: int, low: int) -> int
```

Reconstructs millivolts from high and low bytes.

```python
protocol_decode_millivolts(46, 224)
# → 12000
```

#### `get_millivolts_from_protocol_message`

```python
def get_millivolts_from_protocol_message(
    protocol_message: list[int]
) -> int
```

Decodes a complete 4-byte `GET_VOLTAGE` / `SET_VOLTAGE` response.

Raises `InvalidProtocolMessageLengthError` if `len(protocol_message) != 4`.
Raises `IncorrectCommandByte` if `protocol_message[1] != CMD_GET_VOLTAGE`.

---

### LED state coder — `vflexctl.protocol.coders.led_state`

#### `protocol_decode_led_state`

```python
def protocol_decode_led_state(
    protocol_message: list[int]
) -> bool
```

Decodes a 3-byte `GET_LED_STATE` response.

Returns `False` for always-on (byte 2 is `0x00`), `True` for disabled during operation (byte 2 is `0x01`).

Raises `InvalidProtocolMessageLengthError` if `len(protocol_message) != 3`.
Raises `IncorrectCommandByte` if `protocol_message[1] != CMD_GET_LED_STATE`.

---

### Serial number coder — `vflexctl.protocol.coders.serial_number`

#### `protocol_decode_serial_number`

```python
def protocol_decode_serial_number(
    protocol_message: list[int]
) -> str
```

Decodes a 10-byte `GET_SERIAL_NUMBER` response. The 8 data bytes (positions 2–9) are interpreted as ASCII characters.

Raises `InvalidProtocolMessageLengthError` if `len(protocol_message) != 10`.
Raises `IncorrectCommandByte` if `protocol_message[1] != CMD_GET_SERIAL_NUMBER`.

---

## `vflexctl.command`

### `set_voltage_command`

```python
def set_voltage_command(voltage: int) -> VFlexProtoMessage
```

Returns `[CMD_SET_VOLTAGE, high_byte, low_byte]` for the given millivolt value.

### `get_voltage_command`

```python
def get_voltage_command() -> VFlexProtoMessage
```

Returns `[CMD_GET_VOLTAGE]`.

### `set_led_state_command`

```python
def set_led_state_command(
    value: bool | Literal[0, 1]
) -> VFlexProtoMessage
```

Returns `[CMD_SET_LED_STATE, int(value)]`.

---

## `vflexctl.input_handler.voltage_convert`

### `voltage_to_millivolt`

```python
def voltage_to_millivolt(
    voltage: float | int | str
) -> int
```

Converts a voltage value to integer millivolts. Rounds down to 2 decimal places before multiplying by 1000 to avoid floating-point artefacts.

```python
voltage_to_millivolt(12)        # → 12000
voltage_to_millivolt(5.5)       # → 5500
voltage_to_millivolt(12.0000001)# → 12000  (rounded down to 12.00)
voltage_to_millivolt("12.01")   # → 12010
```

Raises `ValueError` for inputs that cannot be converted to a `Decimal` (e.g. non-numeric strings, `None`, functions).

### `decimal_normalise_voltage`

```python
def decimal_normalise_voltage(
    voltage: float | int | str
) -> Decimal
```

Normalises a voltage to 2 decimal places using `Decimal` arithmetic (rounding down). Returns a `Decimal`.

Raises `ValueError` for unconvertible inputs.

---

## `vflexctl.midi_transport.senders`

### `send_sequence`

```python
def send_sequence(
    output: BaseOutput,
    sequence: list[MIDITriplet]
) -> None
```

Sends a list of MIDI triplets to `output` by calling `send_triplet` for each one in order.

### `send_triplet`

```python
def send_triplet(
    output: BaseOutput,
    triplet_data: MIDITriplet,
    *,
    pause: float = 0.002
) -> None
```

Builds a `mido.Message` from the 3 bytes, sends it via `output.send()`, then sleeps for `pause` seconds.

---

## `vflexctl.midi_transport.receivers`

### `drain_incoming`

```python
def drain_incoming(
    input_port: BaseInput,
    *,
    seconds: float = 0.5
) -> list[MIDITriplet]
```

Polls `input_port` for incoming MIDI messages over a window of `seconds` seconds. Returns all collected messages as a list of triplets.

Returns an empty list immediately if `seconds <= 0`.

### `drain_once`

```python
def drain_once(
    input_port: BaseInput
) -> list[tuple[int, int, int]]
```

Non-blocking: drains all messages currently pending in `input_port` using `iter_pending()` and returns them as a list of byte-tuples. Returns an empty list if nothing is available.

---

## `vflexctl.main`

### `configure_logging`

```python
def configure_logging(verbose: bool, debug: bool) -> None
```

Configures structlog's minimum log level:

| `verbose` | `debug` | Level |
|---|---|---|
| `False` | `False` | `WARNING` |
| `True` | `False` | `INFO` |
| any | `True` | `DEBUG` |

### `main` (Typer callback)

Registered as the `cli.callback()`. Receives the `--verbose` and `--debug` global flags and delegates to `configure_logging`.

---

## `vflexctl.cli`

### `LEDOption(StrEnum)`

Maps CLI flag values to device boolean values.

| Enum member | String value | `bool(x)` | `int(x)` | Meaning |
|---|---|---|---|---|
| `LEDOption.ALWAYS_ON` | `"always-on"` | `False` | `0` | LED stays on (factory default) |
| `LEDOption.DISABLED_DURING_OPERATION` | `"disabled"` | `True` | `1` | LED turns off during normal operation |

### `get_current_v_flex_state` — `vflexctl read`

```
Usage: vflexctl read
```

Connects to the device, runs `wake_up()`, and prints the serial number, current voltage (in volts), and LED state.

### `set_v_flex_state` — `vflexctl set`

```
Usage: vflexctl set [OPTIONS]

Options:
  -v, --voltage FLOAT   Voltage to set, in Volts (e.g 5.00, 12, etc, up to 48.00)
  -l, --led [always-on|disabled]  LED state to set
```

- Voltage must be `> 0`.
- Voltage must not exceed the CLI guard threshold. The guard expression is `voltage > VFLEX_MIDI_INTEGER_LIMIT - 1/1000`. Because Python evaluates `/` before `-`, this computes as `65535 - 0.001 = 65534.999` rather than the apparent intent of `(65535 - 1) / 1000 = 65.534` V. As a result the CLI guard allows any voltage below ~65,535 V, while the README describes the intended ceiling as ~65.5 V. The hard physical ceiling is 65.535 V (65,535 mV), enforced by the 16-bit millivolt encoding.
- At least one of `--voltage` or `--led` must be provided.

Prints a confirmation message before and after the change.
