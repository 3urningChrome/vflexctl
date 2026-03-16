"""Shared structured logger for the protocol package.

Every module inside ``vflexctl.protocol`` should import ``log`` from here
so that all protocol-related log events share a common logger name
(``vflexctl.protocol``) and can be filtered together.
"""

import structlog

__all__ = ["log"]

log = structlog.get_logger("vflexctl.protocol")
