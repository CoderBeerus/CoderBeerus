import unittest
from src.metrics import CalibrationMetrics

class TestCalibrationMetrics(unittest.TestCase):

    def setUp(self):
        """Set up common data for tests."""
        self.ref_values = [10.0, 20.0, 30.0, 40.0, 50.0]
        self.meas_values = [10.1, 20.2, 29.9, 40.0, 50.3]
        self.metrics = CalibrationMetrics(self.ref_values, self.meas_values)
        # Errors will be: [0.1, 0.2, -0.1, 0.0, 0.3]

    def test_initialization(self):
        """Test that the class initializes correctly."""
        self.assertEqual(self.metrics.n, 5)
        self.assertEqual(len(self.metrics.errors), 5)
        with self.assertRaises(ValueError):
            CalibrationMetrics([], [])
        with self.assertRaises(ValueError):
            CalibrationMetrics([1, 2], [1])

    def test_mean_error(self):
        # Expected: (0.1 + 0.2 - 0.1 + 0.0 + 0.3) / 5 = 0.5 / 5 = 0.1
        self.assertAlmostEqual(self.metrics.mean_error(), 0.1, places=4)

    def test_standard_deviation(self):
        # Errors: [0.1, 0.2, -0.1, 0.0, 0.3], Mean: 0.1
        # Squared diffs from mean: [0, 0.01, 0.04, 0.01, 0.04]
        # Sum of sq diffs: 0.1
        # Variance: 0.1 / (5-1) = 0.025
        # Std Dev: sqrt(0.025) = 0.1581
        self.assertAlmostEqual(self.metrics.standard_deviation(), 0.1581, places=4)
        self.assertEqual(self.metrics.precision_index(), self.metrics.standard_deviation())

    def test_rmse(self):
        # Squared errors: [0.01, 0.04, 0.01, 0.0, 0.09]
        # Sum of sq errors: 0.15
        # Mean of sq errors: 0.15 / 5 = 0.03
        # RMSE: sqrt(0.03) = 0.1732
        self.assertAlmostEqual(self.metrics.rmse(), 0.1732, places=4)

    def test_accuracy_percentage(self):
        # Expected: [1.0, 1.0, 0.3333, 0.0, 0.6]
        expected = [
            (0.1 / 10.0) * 100,
            (0.2 / 20.0) * 100,
            (0.1 / 30.0) * 100,
            (0.0 / 40.0) * 100,
            (0.3 / 50.0) * 100,
        ]
        result = self.metrics.accuracy_percentage_vs_reference()
        for i, val in enumerate(expected):
            self.assertAlmostEqual(result[i], val, places=4)

    def test_accuracy_with_zero_ref(self):
        """Test that accuracy calculation handles a zero in reference values."""
        ref = [10.0, 0.0]
        meas = [10.1, 0.1]
        metrics = CalibrationMetrics(ref, meas)
        result = metrics.accuracy_percentage_vs_reference()
        self.assertAlmostEqual(result[0], 1.0)
        self.assertEqual(result[1], float('inf'))

if __name__ == '__main__':
    unittest.main()
