# CALIBRIX Pro
# Main application entry point

from src.simulator import TemperatureSimulator
from src.rtd import rtd_resistance_to_temp
from src.metrics import CalibrationMetrics

def main():
    """Main function to run a test of the calibration system."""
    print("Welcome to CALIBRIX Pro!")
    print("Running a simulation for a PT100 sensor from -20°C to 20°C.")

    # --- Simulation ---
    simulator = TemperatureSimulator(start_temp=-20.0, end_temp=20.0, step=5.0, rtd_type="PT100", noise_level=0.01)

    print("\n--- Point-by-Point Data ---")
    print("{:<15} {:<20} {:<20} {:<15}".format("Ref Temp (°C)", "Measured Res (Ω)", "Calc Temp (°C)", "Error (°C)"))
    print("-" * 75)

    ref_temps = []
    calc_temps = []

    for data_point in simulator:
        ref_temp = data_point["reference_temp"]
        measured_res = data_point["measured_resistance"]

        try:
            calculated_temp = rtd_resistance_to_temp(measured_res, "PT100")
            error = calculated_temp - ref_temp

            ref_temps.append(ref_temp)
            calc_temps.append(calculated_temp)

            print("{:<15.2f} {:<20.4f} {:<20.4f} {:<15.4f}".format(ref_temp, measured_res, calculated_temp, error))
        except (ValueError, NotImplementedError) as e:
            print(f"Could not calculate temperature for {ref_temp}°C: {e}")

    # --- Metrics Calculation ---
    if ref_temps and calc_temps:
        print("\n--- Overall Calibration Metrics ---")
        metrics_calculator = CalibrationMetrics(reference_values=ref_temps, measured_values=calc_temps)

        summary_metrics = metrics_calculator.get_all_metrics()
        for name, value in summary_metrics.items():
            print(f"{name:<25}: {value:.6f}")

        # Display accuracy % for each point
        print("\n--- Accuracy % vs Reference (Point-by-Point) ---")
        accuracy_percentages = metrics_calculator.accuracy_percentage_vs_reference()
        print("{:<15} {:<20}".format("Ref Temp (°C)", "Accuracy (%)"))
        print("-" * 40)
        for i, ref_temp in enumerate(ref_temps):
            print("{:<15.2f} {:<20.4f}".format(ref_temp, accuracy_percentages[i]))


if __name__ == "__main__":
    main()
