"""vflexctl -- CLI and library for controlling VFlex MIDI power adapters.

``vflexctl`` is an unofficial command-line tool (and reusable Python library)
for reading and setting the output voltage and LED behaviour of **Werewolf
Audio VFlex** USB-C power adapters via their MIDI-based control interface.

Quick start (CLI)::

    $ vflexctl read
    $ vflexctl set -v 12 -l always-on

Quick start (library)::

    from vflexctl.device_interface import VFlex

    vflex = VFlex.get_any()
    vflex.initial_wake_up()
    print(vflex.serial_number, vflex.current_voltage)

Package Layout
--------------
protocol/
    Low-level VFlex-over-MIDI protocol: framing constants, message
    parsing, and payload coders (voltage, LED state, hardware info).
command/
    Builders that produce raw protocol messages for each device command.
device_interface/
    High-level :class:`~vflexctl.device_interface.VFlex` class that
    orchestrates MIDI I/O, caches state, and enforces safety checks.
midi_transport/
    Thin wrappers around MIDO for sending and receiving MIDI messages.
input_handler/
    User-input normalisation (e.g. volts → millivolts conversion).
cli.py / main.py
    Typer-based CLI entry-point (``vflexctl read``, ``vflexctl set``).
types.py
    Shared type aliases (``MIDITriplet``, ``VFlexProtoMessage``).
context.py
    Pydantic model for cross-command CLI context.
exceptions.py
    Custom exception hierarchy for protocol and safety errors.
"""
