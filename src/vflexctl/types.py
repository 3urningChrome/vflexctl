"""Shared type aliases used across the vflexctl package.

.. py:type:: MIDITriplet

   ``tuple[int, int, int]`` -- A single 3-byte MIDI message consisting of
   status byte, data byte 1, and data byte 2.

.. py:type:: VFlexProtoMessage

   ``list[int]`` -- A decoded protocol-level message: a list of integer
   bytes where index 0 is the self-describing length and index 1 is the
   command byte.
"""

__all__ = ["MIDITriplet", "VFlexProtoMessage"]

type MIDITriplet = tuple[int, int, int]

type VFlexProtoMessage = list[int]
