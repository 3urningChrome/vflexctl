"""CLI command definitions for vflexctl.

This module creates the :data:`cli` Typer application and registers the
two user-facing sub-commands:

``read``
    Print the current state of the connected VFlex (serial number, voltage,
    LED setting).

``set``
    Modify the output voltage and/or LED behaviour of the connected VFlex.

Helpers
-------
* :class:`LEDOption` -- ``StrEnum`` mapping CLI string values to the
  boolean LED-state the device understands.
* ``_get_app_context`` -- retrieve the :class:`~vflexctl.context.AppContext`
  from the Click context.
* ``_get_connected_v_flex`` -- open a connection to the first available
  VFlex device.
"""

from enum import StrEnum

import click
import typer
from rich import print

from vflexctl.device_interface import VFlex

__all__ = ["cli"]

from vflexctl.input_handler.voltage_convert import decimal_normalise_voltage
from vflexctl.context import AppContext

cli: typer.Typer = typer.Typer(name="vflexctl", no_args_is_help=True)
"""Root Typer application instance used as the CLI entry-point."""

VFLEX_MIDI_INTEGER_LIMIT = 65535
"""Maximum value that can be transmitted as a 16-bit unsigned integer over
the VFlex MIDI protocol (~65.5 V when interpreted as millivolts)."""


class LEDOption(StrEnum):
    """CLI-friendly enum for the two supported LED behaviours.

    The VFlex device LED can be either *always on* (factory default) or
    *disabled during operation* (custom setting).  The ``__bool__`` and
    ``__int__`` overrides ensure these values map naturally to the boolean
    convention used by the protocol layer:

    +--------------------------+--------+------+
    | Member                   | bool() | int()|
    +==========================+========+======+
    | ``ALWAYS_ON``            | False  |  0   |
    +--------------------------+--------+------+
    | ``DISABLED_DURING_OP``   | True   |  1   |
    +--------------------------+--------+------+
    """

    ALWAYS_ON = "always-on"
    DISABLED_DURING_OPERATION = "disabled"

    def __bool__(self) -> bool:
        return self == LEDOption.DISABLED_DURING_OPERATION

    def __int__(self) -> int:
        return int(bool(self))


def _get_app_context() -> AppContext:
    """Retrieve the :class:`AppContext` from the current Click invocation context.

    :raises TypeError: If ``ctx.obj`` is not an :class:`AppContext` instance.
    """
    obj = click.get_current_context().obj
    if not isinstance(obj, AppContext):
        raise TypeError("Context is (somehow) not of the correct type.")
    return obj


def _get_connected_v_flex(full_handshake: bool = False) -> VFlex:
    """Open a MIDI connection to the first available VFlex device.

    :param full_handshake: If ``True``, the device will be initialised with the
        full wake cycle (serial + voltage + LED).
    :return: A :class:`VFlex` instance connected to the device.
    """
    return VFlex.get_any(full_handshake=full_handshake)


def _current_state_str(v_flex: VFlex) -> str:
    """Format a human-readable summary of the device's current state.

    :param v_flex: A VFlex instance that has been woken up (serial, voltage,
        and LED state populated).
    :return: Multi-line string containing serial number, voltage in volts,
        and LED state.
    """
    message = f"""
VFlex Serial Number: {v_flex.serial_number}
Current Voltage: {float(v_flex.current_voltage or 0)/1000:.2f}
LED State: {v_flex.led_state_str}
        """.strip()
    return message


@cli.command(name="read")
def get_current_v_flex_state() -> None:
    """
    Print the current state of the connected VFlex device. (Serial, Voltage & LED setting)
    """
    context = _get_app_context()
    v_flex = _get_connected_v_flex(full_handshake=context.deep_adjust)
    v_flex.initial_wake_up()
    print(_current_state_str(v_flex))


@cli.command(name="set")
def set_v_flex_state(
    voltage: float | None = typer.Option(
        None, "--voltage", "-v", help="Voltage to set, in Volts (e.g 5.00, 12, etc, up to 48.00)"
    ),
    led: LEDOption | None = typer.Option(
        None, "--led", "-l", help='LED state to set, either "on" for always on, or "off" for not always on.'
    ),
) -> None:
    """
    Set voltage and/or LED state for the VFlex device. Prints the state after being set.
    """
    if isinstance(voltage, float | int):
        if voltage > (VFLEX_MIDI_INTEGER_LIMIT - 1 / 1000):
            print(
                "Voltage is being set higher than what can be transmitted. [bold red]The Voltage will not be set.[/bold red]"
            )
            voltage = None
        elif voltage <= 0:
            print("Voltage is being set to 0, or negative. [bold red]The Voltage will not be set.[/bold red]")
            voltage = None
    if voltage is None and led is None:
        print("[bold]You should specify either a valid voltage or LED state to set.[/bold]")
        return None
    context = _get_app_context()
    v_flex = _get_connected_v_flex(full_handshake=context.deep_adjust)
    v_flex.initial_wake_up()
    message: list[str] = []
    if voltage is not None:
        message.append(f"Setting voltage to {decimal_normalise_voltage(voltage)}V")
        # message.append(f"Setting voltage to {float(voltage):.2f}V")
    if led is not None:
        pre_msg = "Setting LED to "
        pre_msg += "be disabled during operation" if bool(led) else "always be on"
        message.append(pre_msg)
    print("\n".join(message))

    if voltage is not None:
        v_flex.set_voltage_volts(voltage)
    if led is not None:
        v_flex.set_led_state(bool(led))

    print("State post set:")
    print(_current_state_str(v_flex))
    return None
