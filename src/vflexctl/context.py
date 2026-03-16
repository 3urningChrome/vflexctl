"""Application context passed between CLI commands via Typer/Click.

The :class:`AppContext` is attached to the Click context object
(``ctx.obj``) inside the global callback in :mod:`vflexctl.main` and is
retrieved by individual CLI commands to access cross-cutting options like
``deep_adjust``.
"""

from pydantic import BaseModel


class AppContext(BaseModel):
    """Pydantic model carrying global CLI flags to every sub-command.

    Attributes
    ----------
    deep_adjust : bool
        When ``True``, the device handshake performs a full wake cycle
        (serial + voltage + LED state) before every mutation.  Corresponds
        to the ``--deep-adjust`` CLI flag.
    """

    # Whether to run the "full handshake" on the VFlex when adjusting.
    deep_adjust: bool
