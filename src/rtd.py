"""
Core RTD Calculation Module

This module provides functions to convert RTD resistance to temperature
based on the IEC 60751 standard (using ITS-90 coefficients).

For temperatures below 0°C, it uses a polynomial correction method inspired by
Uli Koehler's UliEngineering library to achieve high accuracy without complex
iterative solutions.
See: https://github.com/ulikoehler/UliEngineering
And: https://techoverflow.net/2016/01/02/accurate-calculation-of-pt100pt1000-temperature-from-resistance/
"""

import math

# IEC 60751 (ITS-90) coefficients for PT-385
A = 3.9083e-3
B = -5.775e-7
C = -4.183e-12  # For t < 0°C

# R0 values for different RTD types
R0_VALUES = {
    "PT100": 100.0,
    "PT500": 500.0,
    "PT1000": 1000.0,
}

# Pre-computed correction polynomials for t < 0°C.
# The polynomial is applied to the resistance value.
# Format is a list of coefficients for a 5th-degree polynomial.
CORRECTION_POLYNOMIALS = {
    "PT100": [1.51892983e-10, -2.85842067e-08, -5.34227299e-06, 1.80282972e-03, -1.61875985e-01, 4.84112370e+00],
    "PT1000": [1.51892983e-15, -2.85842067e-12, -5.34227299e-09, 1.80282972e-05, -1.61875985e-02, 4.84112370e+00],
    # Note: A polynomial for PT500 would need to be computed.
    # The UliEngineering library provides a function to do this using numpy.
    "PT500": None,
}

def _eval_poly(coeffs, x):
    """Evaluates a polynomial with the given coefficients at x."""
    res = 0
    for p in coeffs:
        res = (res * x) + p
    return res

def rtd_resistance_to_temp(resistance: float, rtd_type: str = "PT100") -> float:
    """
    Calculates temperature in Celsius from RTD resistance.

    Args:
        resistance: The measured resistance of the RTD in ohms.
        rtd_type: The type of RTD ("PT100", "PT500", "PT1000").

    Returns:
        The calculated temperature in Celsius.

    Raises:
        ValueError: If an unsupported RTD type is provided or resistance is invalid.
        NotImplementedError: For PT500 at temperatures below 0°C.
    """
    if rtd_type not in R0_VALUES:
        raise ValueError(f"Unsupported RTD type: {rtd_type}")

    r0 = R0_VALUES[rtd_type]

    # Common quadratic formula part
    # Solves R = R0 * (1 + A*t + B*t^2) for t
    a = r0 * B
    b = r0 * A
    c = r0 - resistance

    discriminant = (b**2) - (4 * a * c)
    if discriminant < 0:
        raise ValueError("Invalid resistance value, results in complex temperature.")

    temp = (-b + math.sqrt(discriminant)) / (2 * a)

    if resistance < r0:
        # For temperatures < 0°C, apply polynomial correction
        poly_coeffs = CORRECTION_POLYNOMIALS.get(rtd_type)
        if poly_coeffs:
            correction = _eval_poly(poly_coeffs, resistance)
            temp += correction
        elif rtd_type == "PT500":
             raise NotImplementedError("Temperature calculation for PT500 below 0°C is not yet implemented. A correction polynomial must be computed.")

    return temp
