# Development Guide

This document covers everything needed to set up a local development environment, run tests, lint the code, and understand how the project is structured for contributions.

---

## Prerequisites

| Tool | Minimum version | Purpose |
|---|---|---|
| Python | 3.12 | Runtime and development |
| [Poetry](https://python-poetry.org/) | 2.0 | Dependency management and packaging |
| [pipx](https://pypa.github.io/pipx/) | any | Isolated tool installation (optional, for end-user install) |
| A VFLEX device | — | Required only for integration/manual testing |

> **Note:** Poetry is required for development. `pipx` is only needed if you want to install the tool for end-user use.

---

## Initial Setup

### 1. Clone the repository

```bash
git clone https://github.com/3urningChrome/vflexctl.git
cd vflexctl
```

### 2. Install dependencies (including dev extras)

```bash
poetry install --with dev
```

This creates a virtual environment and installs:

- All runtime dependencies (`mido`, `python-rtmidi`, `typer`, `rich`, `colorama`, `structlog`)
- Development tools (`pytest`, `pytest-mock`, `black`, `mypy`)

### 3. Activate the virtual environment

```bash
poetry shell
```

Or prefix individual commands with `poetry run`.

---

## Running the Tool Locally

```bash
# Using the Poetry-managed environment
poetry run vflexctl read
poetry run vflexctl set -v 12 -l always-on

# Inside an active `poetry shell`
vflexctl read
```

---

## Testing

Tests live in `test/unit/` and mirror the `src/vflexctl/` package layout. The test framework is **pytest** with **pytest-mock** for mocking.

### Run all tests

```bash
poetry run pytest
```

### Run tests for a specific module

```bash
# Protocol codec tests
poetry run pytest test/unit/protocol/

# VFlex device interface tests
poetry run pytest test/unit/device_interface/

# Voltage conversion tests
poetry run pytest test/unit/input_handler/

# MIDI transport tests
poetry run pytest test/unit/midi_transport/
```

### Run a single test file

```bash
poetry run pytest test/unit/protocol/coders/test_voltage_coders.py
```

### Run with verbose output

```bash
poetry run pytest -v
```

### Test layout

```
test/
└── unit/
    ├── device_interface/
    │   └── test_vflex.py              ← VFlex class: wake-up, get/set voltage, get/set LED, safe-adjust
    ├── input_handler/
    │   └── test_voltage_convert.py    ← voltage_to_millivolt, edge cases
    ├── midi_transport/
    │   ├── test_midi_receivers.py     ← drain_once, drain_incoming
    │   └── test_midi_senders.py       ← send_triplet, send_sequence
    └── protocol/
        ├── coders/
        │   ├── test_led_state_coders.py
        │   ├── test_serial_number_coders.py
        │   └── test_voltage_coders.py
        ├── test_command_framing.py
        └── test_protocol.py
```

### Writing new tests

Follow the existing conventions:

- Use `pytest` fixtures defined within the test file.
- Use `mocker.patch("vflexctl.<module>.<name>")` (not `unittest.mock.patch`) to mock dependencies.
- Use `mocker.MagicMock()` for the MIDI `io_port`.
- To test a method decorated with `@run_with_handshake`, access the unwrapped function via `VFlex.<method>.__wrapped__(instance, ...)`.

Example:

```python
def test_get_voltage_updates_self_and_returns(mocker, mock_io_port):
    mocker.patch("vflexctl.device_interface.vflex.send_sequence")
    mocker.patch("vflexctl.device_interface.vflex.drain_incoming", return_value=["midi-bytes"])
    mocker.patch(
        "vflexctl.device_interface.vflex.protocol_message_from_midi_messages",
        return_value=[4, 18, 0x2E, 0xE0],
    )
    mocker.patch(
        "vflexctl.device_interface.vflex.get_millivolts_from_protocol_message",
        return_value=12000,
    )

    v_flex = VFlex(mock_io_port, safe_adjust=False)
    result = VFlex.get_voltage.__wrapped__(v_flex, update_self=True)

    assert result == 12000
    assert v_flex.current_voltage == 12000
```

---

## Linting and Formatting

### Black (code formatter)

The project uses [Black](https://black.readthedocs.io/) with a line length of 120 characters targeting Python 3.13.

```bash
# Check formatting without modifying files
poetry run black --check src/ test/

# Apply formatting
poetry run black src/ test/
```

Black configuration is in `pyproject.toml`:

```toml
[tool.black]
line-length = 120
target-version = ['py313']
```

### mypy (static type checker)

The project uses [mypy](https://mypy.readthedocs.io/) in strict mode.

```bash
poetry run mypy src/
```

mypy configuration is in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
warn_unused_configs = true
strict = true
```

The `mido` package does not ship type stubs, so it is excluded from strict checking:

```toml
[[tool.mypy.overrides]]
module = "mido.*"
ignore_missing_imports = true
```

---

## Project Configuration (`pyproject.toml`)

### Entry point

```toml
[project.scripts]
vflexctl = "vflexctl.main:cli"
```

The installed command `vflexctl` calls the `cli` Typer app object defined in `main.py`.

### Package source

```toml
[tool.poetry]
packages = [
    { include = "vflexctl", from = "src" },
]
```

The package is located under `src/vflexctl/` (src-layout), which keeps the package code isolated from project-level files.

### Runtime dependencies

| Package | Version constraint | Role |
|---|---|---|
| `python-rtmidi` | `>=1.5.8,<2.0.0` | Native MIDI I/O backend |
| `mido` | `>=1.3.3,<2.0.0` | High-level MIDI abstraction over rtmidi |
| `typer` | `>=0.20.0,<0.21.0` | CLI framework |
| `rich` | `>=14.2.0,<15.0.0` | Rich terminal output |
| `colorama` | `>=0.4.6,<0.5.0` | Cross-platform ANSI colours (required by Rich on Windows) |
| `structlog` | `>=25.5.0,<26.0.0` | Structured logging |

### Development dependencies

| Package | Version constraint | Role |
|---|---|---|
| `pytest` | `>=9.0.1,<10.0.0` | Test runner |
| `pytest-mock` | `>=3.15.1,<4.0.0` | `mocker` fixture for pytest |
| `black` | `>=25.11.0,<26.0.0` | Code formatter |
| `mypy` | `>=1.19.0,<2.0.0` | Static type checker |

---

## Logging

vflexctl uses [structlog](https://www.structlog.org/) throughout. Log levels are set globally at startup via `configure_logging` in `main.py`.

To see detailed logs during development:

```bash
vflexctl --debug read
vflexctl --verbose set -v 12
```

Individual modules each create their own logger:

| Module | Logger name |
|---|---|
| `device_interface/vflex.py` | `vflexctl.VFlex` |
| `midi_transport/senders.py` | `vflexctl.midi_senders` |
| `midi_transport/receivers.py` | `vflexctl.midi_receivers` |
| `protocol/logger.py` | `vflexctl.protocol` |
| `input_handler/voltage_convert.py` | (root logger) |

---

## Adding a New Command

To add support for a new VFlex protocol command, follow these steps:

1. **Add the command byte** to `VFlexProto` in `protocol/protocol.py`.
2. **Create a command builder** in `command/` (following the pattern in `voltage.py` or `led.py`).
3. **Create a decoder** in `protocol/coders/` (following the pattern in `voltage.py`).
4. **Add a pre-built sequence** to `device_interface/common_sequences.py` if it's a read operation.
5. **Add a method** to `VFlex` in `device_interface/vflex.py`.
6. **Expose the method** via the CLI in `cli.py` if it needs to be user-facing.
7. **Add tests** in `test/unit/` for each new function.

---

## Building and Publishing

```bash
# Build source distribution and wheel
poetry build

# Publish to PyPI (requires credentials)
poetry publish
```

---

## Known Issues and Future Work

The following items are noted in the original README as potential improvements:

- **Single device selection.** There is currently no mechanism to select a specific device when multiple VFLEX adapters are connected.
- **Wake-up optimisation.** The full three-step wake-up sequence runs before every operation. In practice, if operations complete in under ~5 seconds the device may still be awake, making the serial and LED reads unnecessary.
- **MIDI heartbeat.** The vendor web app sends a MIDI Clock message every ~6 seconds. vflexctl does not replicate this; the impact on device behaviour over long-running sessions is unknown.
