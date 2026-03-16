"""VFlex-over-MIDI protocol implementation.

Public API re-exported here for convenience:

* :class:`VFlexProto` -- framing sentinels and command-ID constants.
* :func:`protocol_message_from_midi_messages` -- decode MIDI triples into
  a validated protocol message.
* :func:`prepare_command_frame` -- prepend the length byte to a sub-command.
* :func:`prepare_command_for_sending` -- convert a framed command into a
  list of MIDI triplets ready to transmit.

See Also
--------
vflexctl.protocol.coders : Encode / decode payload fields (voltage,
    serial number, LED state, firmware version).
"""

from .protocol import VFlexProto, protocol_message_from_midi_messages
from .command_framing import prepare_command_frame, prepare_command_for_sending

__all__ = ["VFlexProto", "protocol_message_from_midi_messages", "prepare_command_frame", "prepare_command_for_sending"]
