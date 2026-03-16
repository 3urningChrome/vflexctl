"""High-level device interface for VFlex MIDI power adapters.

The main public class is :class:`VFlex`, which wraps a MIDO I/O port and
provides methods to query and configure the adapter (voltage, LED state,
serial number, firmware version).

Example::

    from vflexctl.device_interface import VFlex

    vflex = VFlex.get_any()
    vflex.initial_wake_up()
    print(vflex.serial_number, vflex.current_voltage)
"""

from .vflex import VFlex

__all__ = ["VFlex"]
