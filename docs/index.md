# vflexctl Documentation

**vflexctl** is an unofficial command-line tool for controlling [VFLEX](https://www.vflex.com/) power-adapter devices via MIDI. It lets you read and set the output voltage and LED behaviour of a connected VFLEX device without needing the vendor's web interface.

- **Version:** 0.1.2
- **License:** Apache 2.0
- **Python requirement:** ≥ 3.12, < 4.0

---

## Documentation Contents

| Document | Description |
|---|---|
| [Architecture](architecture.md) | Module layout, component responsibilities, data-flow |
| [Protocol](protocol.md) | Low-level VFlex MIDI protocol specification |
| [API Reference](api-reference.md) | Complete reference for every module, class, and function |
| [Development Guide](development.md) | Setup, testing, linting, and contributing |

---

## Quick Start

### Prerequisites

- Python 3.12 or newer
- [`pipx`](https://pypa.github.io/pipx/) for isolated installation
- A VFLEX power adapter connected via USB (it presents as a MIDI device named **"Werewolf vFlex"**)

### Installation

```bash
pipx install vflexctl
```

### Reading the current device state

```bash
vflexctl read
```

Example output:

```
VFlex Serial Number: A1B2C3D4
Current Voltage: 12.00
LED State: always on
```

### Setting voltage and/or LED state

```bash
# Set voltage to 12 V
vflexctl set -v 12

# Set voltage to 5.5 V
vflexctl set -v 5.5

# Set LED to always-on (factory default)
vflexctl set -l always-on

# Disable the LED during normal operation
vflexctl set -l disabled

# Set both voltage and LED in one call
vflexctl set -v 24 -l always-on
```

### Global flags

| Flag | Default | Description |
|---|---|---|
| `--verbose` | off | Enable INFO-level logging via structlog |
| `--debug` | off | Enable DEBUG-level logging via structlog |

---

## Constraints and Known Limitations

- **Single device only.** When more than one VFLEX is connected there is no guarantee the same device will be selected across invocations.
- **Voltage ceiling.** The MIDI millivolt encoding uses a 16-bit integer, so the true maximum settable voltage is 65.535 V (65,535 mV). The CLI guard expression is `voltage > VFLEX_MIDI_INTEGER_LIMIT - 1/1000`; because Python evaluates `/` before `-`, this resolves to `voltage > 65534.999` rather than the apparent intent of `voltage > (65535 - 1) / 1000` (= 65.534 V). Voltages above 65.535 V will overflow the 16-bit encoding silently.
- **Voltage floor.** Attempting to set 0 V or a negative voltage is rejected.
- **Startup dance.** Every `set` or `get_*` call first runs a wake-up sequence (serial → LED → voltage) to confirm the device is ready and the expected device is still present. This makes operations slightly slower than the web interface.
- **Safe-adjust mode.** By default, the library re-reads the serial number before every mutating operation and aborts if it has changed. This prevents accidentally modifying a different device.

---

## Project Layout

```
vflexctl/
├── docs/                         ← this documentation
├── src/
│   └── vflexctl/                 ← installable package
│       ├── main.py               ← CLI entry-point & logging setup
│       ├── cli.py                ← Typer commands (read, set)
│       ├── types.py              ← shared type aliases
│       ├── exceptions.py         ← custom exception hierarchy
│       ├── device_interface/     ← high-level VFlex device API
│       ├── protocol/             ← VFlex protocol codec
│       ├── command/              ← protocol command builders
│       ├── input_handler/        ← user-input normalisation
│       └── midi_transport/       ← low-level MIDI send/receive
├── test/
│   └── unit/                     ← pytest unit tests (mirrors src layout)
├── pyproject.toml
├── poetry.lock
└── readme.rst
```
