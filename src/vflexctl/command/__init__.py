"""Command builders for VFlex protocol operations.

Each sub-module produces a raw *protocol message* (a ``list[int]``) for a
specific device command.  The caller is expected to pass the result through
:func:`vflexctl.protocol.prepare_command_frame` and
:func:`vflexctl.protocol.prepare_command_for_sending` before transmitting.

Available commands
------------------
* :func:`get_voltage_command` / :func:`set_voltage_command` -- voltage
  queries and mutations.
* :func:`set_led_state_command` -- set the device LED behaviour.
* ``get_firmware_version_command`` / ``get_hardware_revision_command`` --
  hardware identification (in :mod:`.hardware_info`).
"""

from .led import set_led_state_command
from .voltage import get_voltage_command, set_voltage_command

__all__ = ["get_voltage_command", "set_voltage_command", "set_led_state_command"]
