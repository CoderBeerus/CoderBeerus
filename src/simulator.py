"""
Temperature Simulator Module

This module provides a simulator to generate realistic RTD temperature and
resistance data for testing and development purposes.
"""

import time
import random
from src.rtd import R0_VALUES, A, B, C

def rtd_temp_to_resistance(temperature: float, rtd_type: str = "PT100") -> float:
    """
    Calculates RTD resistance from temperature in Celsius.
    This is the forward calculation, inverse of rtd_resistance_to_temp.

    Args:
        temperature: The temperature in Celsius.
        rtd_type: The type of RTD ("PT100", "PT500", "PT1000").

    Returns:
        The calculated resistance in ohms.

    Raises:
        ValueError: If an unsupported RTD type is provided.
    """
    if rtd_type not in R0_VALUES:
        raise ValueError(f"Unsupported RTD type: {rtd_type}")

    r0 = R0_VALUES[rtd_type]

    c_val = C if temperature < 0 else 0.0

    resistance = r0 * (1 + A * temperature + B * temperature**2 + c_val * (temperature - 100) * temperature**3)
    return resistance

class TemperatureSimulator:
    """
    A class to simulate temperature and resistance data from an RTD sensor.
    """
    def __init__(self, start_temp=-50.0, end_temp=200.0, step=1.0, rtd_type="PT100", noise_level=0.01):
        """
        Initializes the simulator.

        Args:
            start_temp: The starting temperature in Celsius.
            end_temp: The ending temperature in Celsius.
            step: The temperature step for each iteration.
            rtd_type: The type of RTD to simulate.
            noise_level: The standard deviation of the noise to add to the resistance.
        """
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.step = step
        self.rtd_type = rtd_type
        self.noise_level = noise_level
        self.current_temp = start_temp

    def __iter__(self):
        self.current_temp = self.start_temp
        return self

    def __next__(self):
        """
        Generates the next data point from the simulator.
        """
        if self.current_temp > self.end_temp:
            raise StopIteration

        # Calculate ideal resistance
        ideal_resistance = rtd_temp_to_resistance(self.current_temp, self.rtd_type)

        # Add some noise
        noise = random.normalvariate(0, self.noise_level)
        measured_resistance = ideal_resistance + noise

        # Create data point
        data_point = {
            "timestamp": time.time(),
            "reference_temp": self.current_temp,
            "measured_resistance": measured_resistance,
        }

        # Increment temperature for next iteration
        self.current_temp += self.step

        return data_point
