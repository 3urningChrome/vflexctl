"""Voltage payload encoder/decoder for the VFlex protocol.

Voltage is represented as an unsigned 16-bit integer giving the value in
**millivolts** (e.g. 12 000 mV = 12.00 V).  On the wire it occupies two
protocol bytes arranged big-endian: ``[high_byte, low_byte]``.

The protocol message layout for a voltage response is::

    [length=4, CMD_GET_VOLTAGE (0x12), high_byte, low_byte]

Functions
---------
protocol_encode_millivolts
    ``int -> (high, low)``
protocol_decode_millivolts
    ``(high, low) -> int``
get_millivolts_from_protocol_message
    Validate a full protocol response and extract the millivolt value.
"""

__all__ = ["protocol_encode_millivolts", "protocol_decode_millivolts", "get_millivolts_from_protocol_message"]

from vflexctl.exceptions import InvalidProtocolMessageLengthError, IncorrectCommandByte
from vflexctl.protocol import VFlexProto


def protocol_encode_millivolts(value: int) -> tuple[int, int]:
    """
    Encodes millivolts into the two protocol bytes needed to send it, split
    into the high and low bytes for the voltage.

    When transporting, these bytes are then sent as high and low nibbles.

    :param value: The value to encode into the protocol.
    :return: The tuple of high and low bytes.
    """
    high_byte = (value >> 8) & 0xFF
    low_byte = value & 0xFF
    return high_byte, low_byte


def protocol_decode_millivolts(high: int, low: int) -> int:
    """
    Decode the two protocol bytes from a set/get voltage response into the millivolts.

    :param high: The high byte value.
    :param low: The low byte value.
    :return:
    """
    return high << 8 | low


def get_millivolts_from_protocol_message(protocol_message: list[int]) -> int:
    """
    Decode a protocol response from a get/set voltage command, and get the millivolts from
    the response.

    :param protocol_message: The protocol message to decode
    :return: The millivolts from the response
    """
    if len(protocol_message) != 4:
        raise InvalidProtocolMessageLengthError(protocol_message, 4)
    if protocol_message[1] != VFlexProto.CMD_GET_VOLTAGE:
        raise IncorrectCommandByte(protocol_message, VFlexProto.CMD_GET_VOLTAGE)
    return protocol_decode_millivolts(protocol_message[2], protocol_message[3])
