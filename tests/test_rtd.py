import unittest
import math
from src.rtd import rtd_resistance_to_temp
from src.simulator import rtd_temp_to_resistance

class TestRTDCalculations(unittest.TestCase):

    def test_roundtrip_consistency_pt100(self):
        """
        Tests if converting temp to resistance and back yields the original temp for PT100.
        """
        temperatures_to_test = [-200, -100, -20, 0, 50, 100, 200, 850]
        for temp in temperatures_to_test:
            with self.subTest(temp=temp):
                resistance = rtd_temp_to_resistance(temp, "PT100")
                calculated_temp = rtd_resistance_to_temp(resistance, "PT100")
                self.assertAlmostEqual(calculated_temp, temp, places=4, msg=f"Failed for {temp}°C")

    def test_roundtrip_consistency_pt1000(self):
        """
        Tests if converting temp to resistance and back yields the original temp for PT1000.
        """
        temperatures_to_test = [-200, -100, -20, 0, 50, 100, 200, 850]
        for temp in temperatures_to_test:
            with self.subTest(temp=temp):
                resistance = rtd_temp_to_resistance(temp, "PT1000")
                calculated_temp = rtd_resistance_to_temp(resistance, "PT1000")
                self.assertAlmostEqual(calculated_temp, temp, places=4, msg=f"Failed for {temp}°C")

    def test_invalid_rtd_type_exception(self):
        """Tests that an invalid RTD type raises a ValueError."""
        with self.assertRaises(ValueError):
            rtd_resistance_to_temp(100.0, "PT999")

    def test_pt500_not_implemented_exception(self):
        """Tests that PT500 below 0°C raises a NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            # Resistance for PT500 at -20°C would be approx 460.8 ohms
            rtd_resistance_to_temp(460.0, "PT500")

    def test_pt500_positive_temp(self):
        """Tests that PT500 works for positive temperatures."""
        # At 100C, R should be 500 * 1.385055 = 692.5275
        self.assertAlmostEqual(rtd_resistance_to_temp(692.5275, "PT500"), 100.0, places=4)


if __name__ == '__main__':
    unittest.main()
