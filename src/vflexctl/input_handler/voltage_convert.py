"""Voltage conversion and normalisation utilities.

User-facing voltage values are in **volts** (e.g. ``12.0``, ``5.50``),
but the VFlex protocol operates in **millivolts** (``12000``, ``5500``).
This module provides:

* :func:`voltage_to_millivolt` -- convert a human-readable voltage to an
  integer millivolt value suitable for the protocol layer.
* :func:`decimal_normalise_voltage` -- normalise a voltage to a
  :class:`~decimal.Decimal` rounded to 2 decimal places (centivolt
  precision) for display purposes.

All conversions use the :mod:`decimal` module to avoid floating-point
rounding artefacts.
"""

from decimal import Decimal, InvalidOperation, ROUND_DOWN

import structlog

__all__ = ["voltage_to_millivolt", "decimal_normalise_voltage"]

log = structlog.get_logger()


def voltage_to_millivolt(voltage: float | int | str) -> int:
    """
    Takes in a number representing a voltage and converts it to millivolts.

    :param voltage: A float or integer for the voltage. Expects a voltage
        that goes to at most 2 decimal places, and will round a voltage provided
        that's longer than 2 decimal places.
    :return: Integer representing the voltage in millivolts.
    """
    normalised_decimal = decimal_normalise_voltage(voltage)
    rounded_voltage: Decimal = normalised_decimal.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    millivolts = int((rounded_voltage * 1000).to_integral_value(rounding=ROUND_DOWN))
    return millivolts


def decimal_normalise_voltage(voltage: float | int | str) -> Decimal:
    """
    Takes in a voltage to any number of decimals, and converts it to a voltage to 2 decimal places.
    :param voltage: The voltage to normalise.
    :return: Decimal value, rounded to 2 decimal places.
    """
    try:
        normalised = Decimal(str(voltage))
    except (InvalidOperation, ValueError, TypeError) as e:
        log.exception(
            "Got a value that cannot be converted to a Decimal.",
            exc_info=e,
            value=voltage,
            value_type=type(voltage).__name__,
        )
        raise ValueError("This function requires values that can be converted to decimals.") from e
    return normalised.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
