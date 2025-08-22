"""
Metrics Calculation Module

This module provides a class to calculate various calibration metrics based on
a series of reference and measured values.
"""

import math

class CalibrationMetrics:
    """
    Calculates and holds various calibration metrics.
    """
    def __init__(self, reference_values: list[float], measured_values: list[float]):
        """
        Initializes the metrics calculator with reference and measured data.

        Args:
            reference_values: A list of reference (true) values.
            measured_values: A list of corresponding measured values.

        Raises:
            ValueError: If the input lists are empty or have different lengths.
        """
        if not reference_values or not measured_values:
            raise ValueError("Input lists cannot be empty.")
        if len(reference_values) != len(measured_values):
            raise ValueError("Reference and measured value lists must have the same length.")

        self.reference_values = reference_values
        self.measured_values = measured_values
        self.errors = [m - r for m, r in zip(measured_values, reference_values)]
        self.n = len(self.errors)

    def mean_error(self) -> float:
        """Calculates the Mean Error (or Mean Bias Error)."""
        return sum(self.errors) / self.n

    def standard_deviation(self) -> float:
        """
        Calculates the standard deviation of the errors.
        This is used as the 'Precision Index'.
        """
        if self.n < 2:
            return 0.0  # Std dev is not defined for a single data point

        mean = self.mean_error()
        variance = sum([(e - mean) ** 2 for e in self.errors]) / (self.n - 1)
        return math.sqrt(variance)

    def rmse(self) -> float:
        """Calculates the Root Mean Square Error."""
        return math.sqrt(sum([e ** 2 for e in self.errors]) / self.n)

    def precision_index(self) -> float:
        """
        Returns the Precision Index, which is defined as the standard deviation of the errors.
        """
        return self.standard_deviation()

    def accuracy_percentage_vs_reference(self) -> list[float]:
        """
        Calculates the accuracy as a percentage of the reference value for each point.
        Formula: (|Measured - Reference| / |Reference|) * 100

        Returns:
            A list of accuracy percentages. Returns float('inf') for a point if the
            reference value is 0.
        """
        percentages = []
        for r, m in zip(self.reference_values, self.measured_values):
            if r == 0:
                percentages.append(float('inf')) # Or handle as a special case
            else:
                percentages.append((abs(m - r) / abs(r)) * 100)
        return percentages

    def get_all_metrics(self) -> dict:
        """
        Returns a dictionary containing all calculated summary metrics.
        """
        return {
            "mean_error": self.mean_error(),
            "rmse": self.rmse(),
            "precision_index (std_dev)": self.precision_index(),
        }
