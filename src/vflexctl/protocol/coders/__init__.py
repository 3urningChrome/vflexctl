"""Payload encoders and decoders for VFlex protocol messages.

Each sub-module handles one *family* of commands:

* **voltage** -- encode/decode 16-bit millivolt values to/from the two
  payload bytes used by ``CMD_GET_VOLTAGE`` / ``CMD_SET_VOLTAGE``.
* **led_state** -- decode the single-byte LED-state payload returned by
  ``CMD_GET_LED_STATE``.
* **hardware_info** -- decode ASCII payloads for serial number, hardware
  revision, and firmware version.

All public symbols are re-exported from this ``__init__`` for convenience.
"""

from .voltage import protocol_encode_millivolts, protocol_decode_millivolts, get_millivolts_from_protocol_message
from .led_state import protocol_decode_led_state
from .hardware_info import (
    protocol_decode_serial_number,
    protocol_decode_hardware_revision,
    protocol_decode_firmware_version,
)

__all__ = [
    "protocol_decode_millivolts",
    "protocol_encode_millivolts",
    "get_millivolts_from_protocol_message",
    "protocol_decode_led_state",
    "protocol_decode_serial_number",
    "protocol_decode_hardware_revision",
    "protocol_decode_firmware_version",
]
