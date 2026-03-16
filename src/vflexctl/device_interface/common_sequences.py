"""Pre-built MIDI command sequences for common read-only queries.

These module-level constants avoid repeatedly constructing the same
framed-and-encoded MIDI sequences every time the device is polled for its
serial number, LED state, or current voltage.  Each constant is a
``list[tuple[int, int, int]]`` ready to be passed directly to
:func:`vflexctl.midi_transport.senders.send_sequence`.
"""

from vflexctl.protocol import VFlexProto, prepare_command_for_sending, prepare_command_frame

__all__ = ["GET_VOLTAGE_SEQUENCE", "GET_LED_STATE_SEQUENCE", "GET_SERIAL_NUMBER_SEQUENCE"]

type CommandList = list[tuple[int, int, int]]

GET_SERIAL_NUMBER_SEQUENCE: CommandList = prepare_command_for_sending(
    prepare_command_frame([VFlexProto.CMD_GET_SERIAL_NUMBER])
)
"""MIDI sequence to request the device serial number."""

GET_LED_STATE_SEQUENCE: CommandList = prepare_command_for_sending(prepare_command_frame([VFlexProto.CMD_GET_LED_STATE]))
"""MIDI sequence to request the current LED-state setting."""

GET_VOLTAGE_SEQUENCE: CommandList = prepare_command_for_sending(prepare_command_frame([VFlexProto.CMD_GET_VOLTAGE]))
"""MIDI sequence to request the current output voltage."""
