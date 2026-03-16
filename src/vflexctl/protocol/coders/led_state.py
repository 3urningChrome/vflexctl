"""LED-state payload decoder for the VFlex protocol.

The LED-state response from the device is a single byte:

* ``0x00`` (``False``) -- LED is **always on** (factory default).
* ``0x01`` (``True``)  -- LED is **disabled during operation**.

The full protocol message layout is::

    [length=3, CMD_GET_LED_STATE (0x0F), state_byte]
"""

from vflexctl.exceptions import InvalidProtocolMessageLengthError, IncorrectCommandByte
from vflexctl.protocol import VFlexProto

__all__ = ["protocol_decode_led_state"]


def protocol_decode_led_state(protocol_message: list[int]) -> bool:
    """
    Decodes the LED state from returned data. True means that the LED is not "always on" (non-default behaviour).
    False means that the LED is always on (factory default behaviour).

    :param protocol_message: The protocol message to decode.
    :return: Boolean value indicating the LED state.
    """
    if len(protocol_message) != 3:
        raise InvalidProtocolMessageLengthError(protocol_message, 3)
    if protocol_message[1] != VFlexProto.CMD_GET_LED_STATE:
        raise IncorrectCommandByte(protocol_message, VFlexProto.CMD_GET_LED_STATE)
    return bool(protocol_message[2])
