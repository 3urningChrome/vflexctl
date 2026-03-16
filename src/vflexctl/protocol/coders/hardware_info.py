"""Hardware-information payload decoders for the VFlex protocol.

These functions decode the ASCII payloads returned by the device for
hardware identification queries:

* **Serial number** (``CMD_GET_SERIAL_NUMBER``, ``0x08``) -- 8-character
  ASCII string.  Protocol message: ``[10, 0x08, c0, c1, ..., c7]``.
* **Hardware revision** (``CMD_GET_HARDWARE_REVISION``, ``0x0A``) --
  variable-length ASCII string.
* **Firmware version** (``CMD_GET_FIRMWARE_VERSION``, ``0x0B``) -- 12-byte
  ASCII string in the format ``APP.##.##.##``.  Protocol message:
  ``[14, 0x0B, <12 ASCII bytes>]``.
"""

from vflexctl.exceptions import InvalidProtocolMessageLengthError, IncorrectCommandByte
from vflexctl.protocol import VFlexProto

__all__ = [
    "protocol_decode_serial_number",
    "protocol_decode_hardware_revision",
    "protocol_decode_firmware_version",
]


def protocol_decode_serial_number(protocol_message: list[int]) -> str:
    """Decode the device serial number from a ``CMD_GET_SERIAL_NUMBER`` response.

    The serial number is an 8-character ASCII string located at bytes 2-9
    of a 10-byte protocol message.

    :param protocol_message: Validated protocol message (length 10).
    :return: The serial number as a Python string.
    :raises InvalidProtocolMessageLengthError: If the message is not exactly 10 bytes.
    :raises IncorrectCommandByte: If the command byte is not ``CMD_GET_SERIAL_NUMBER``.
    """
    if len(protocol_message) != 10:
        raise InvalidProtocolMessageLengthError(protocol_message, 10)
    if protocol_message[1] != VFlexProto.CMD_GET_SERIAL_NUMBER:
        raise IncorrectCommandByte(protocol_message, VFlexProto.CMD_GET_SERIAL_NUMBER)
    return bytearray(protocol_message[2:]).decode()


def protocol_decode_hardware_revision(protocol_message: list[int]) -> str:
    """Decode the hardware revision from a ``CMD_GET_HARDWARE_REVISION`` response.

    The revision is a variable-length ASCII string starting at byte 2.

    :param protocol_message: Validated protocol message.
    :return: The hardware revision as a Python string.
    :raises IncorrectCommandByte: If the command byte is not ``CMD_GET_HARDWARE_REVISION``.
    """
    if protocol_message[1] != VFlexProto.CMD_GET_HARDWARE_REVISION:
        raise IncorrectCommandByte(protocol_message, VFlexProto.CMD_GET_HARDWARE_REVISION)
    return bytearray(protocol_message[2:]).decode()


def protocol_decode_firmware_version(protocol_message: list[int]) -> str:
    """Decode the firmware version from a ``CMD_GET_FIRMWARE_VERSION`` response.

    The version string is 12 ASCII characters in the format ``APP.##.##.##``
    (where ``#`` is a digit) contained in a 14-byte protocol message.

    :param protocol_message: Validated protocol message (length 14).
    :return: The firmware version as a Python string (e.g. ``"APP.04.00.00"``).
    :raises InvalidProtocolMessageLengthError: If the message is not exactly 14 bytes.
    :raises IncorrectCommandByte: If the command byte is not ``CMD_GET_FIRMWARE_VERSION``.
    """
    if len(protocol_message) != 14:
        raise InvalidProtocolMessageLengthError(protocol_message, 14)
    if protocol_message[1] != VFlexProto.CMD_GET_FIRMWARE_VERSION:
        raise IncorrectCommandByte(protocol_message, VFlexProto.CMD_GET_FIRMWARE_VERSION)
    return bytearray(protocol_message[2:]).decode()
