# main.py

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import machine
import time
import ujson
# Add other necessary imports like specific sensor libraries (e.g., dht, bmp280)
# import dht
# import bmp280
# from onewire import OneWire
# from ds18x20 import DS18X20

# -----------------------------------------------------------------------------
# Global Variables & Constants
# -----------------------------------------------------------------------------
# --- Serial Communication ---
UART_BAUD_RATE = 115200
UART_ID = 0  # Or 1, 2 depending on ESP32 pins used
uart = None  # Will be initialized in setup_serial()

# --- Sensor Configuration ---
# Define a dictionary to hold sensor configurations.
# Each key could be a sensor ID or name.
# Values could be objects or dictionaries detailing pin, type, address, etc.
# Example:
# SENSOR_CONFIG = {
#     "temp_humidity_1": {"type": "DHT22", "pin": 4, "instance": None},
#     "pressure_1": {"type": "BMP280", "scl_pin": 22, "sda_pin": 21, "instance": None},
#     "ds18b20_1": {"type": "DS18B20", "pin": 5, "instance": None, "roms": []},
#     "analog_sensor_1": {"type": "ANALOG", "pin": 32, "name": "dp_transmitter_input", "attenuation": "11DB", "instance": None}
# }
SENSOR_CONFIG = {} # To be populated by configuration received via serial

# --- Timing ---
MAIN_LOOP_DELAY_MS = 1000  # Delay in milliseconds for the main loop

# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------
# (Potentially define custom classes here if needed, e.g., for complex sensor data)

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def initialize_sensors():
    """
    Initializes sensor objects based on SENSOR_CONFIG.
    This function will populate the 'instance' field in SENSOR_CONFIG.
    """
    global SENSOR_CONFIG
    print("Initializing sensors...")
    for sensor_id, config in SENSOR_CONFIG.items():
        try:
            if config["type"] == "DHT22":
                # Placeholder for DHT22 initialization
                # config["instance"] = dht.DHT22(machine.Pin(config["pin"]))
                print(f"  {sensor_id} (DHT22) on pin {config['pin']} initialized.")
            elif config["type"] == "BMP280":
                # Placeholder for BMP280 initialization
                # i2c = machine.I2C(0, scl=machine.Pin(config["scl_pin"]), sda=machine.Pin(config["sda_pin"]))
                # config["instance"] = bmp280.BMP280(i2c)
                print(f"  {sensor_id} (BMP280) on SCL:{config['scl_pin']}, SDA:{config['sda_pin']} initialized.")
            elif config["type"] == "DS18B20":
                # Placeholder for DS18B20 initialization
                # ow = OneWire(machine.Pin(config["pin"]))
                # ds = DS18X20(ow)
                # config["roms"] = ds.scan()
                # config["instance"] = ds
                print(f"  {sensor_id} (DS18B20) on pin {config['pin']} initialized. Found ROMs: {config.get('roms', [])}")
            elif config["type"] == "ANALOG":
                # Placeholder for Analog ADC initialization
                # adc_pin = machine.Pin(config["pin"])
                # adc = machine.ADC(adc_pin)
                #
                # # Set attenuation based on config - crucial for voltage range
                # # Options: machine.ADC.ATTN_0DB (1.2V), machine.ADC.ATTN_2_5DB (1.5V),
                # #          machine.ADC.ATTN_6DB (2.0V), machine.ADC.ATTN_11DB (3.3V max)
                # if config.get("attenuation") == "0DB":
                #     # adc.atten(machine.ADC.ATTN_0DB)
                #     pass
                # elif config.get("attenuation") == "2_5DB":
                #     # adc.atten(machine.ADC.ATTN_2_5DB)
                #     pass
                # elif config.get("attenuation") == "6DB":
                #     # adc.atten(machine.ADC.ATTN_6DB)
                #     pass
                # elif config.get("attenuation") == "11DB": # Default for full range up to 3.3V
                #     # adc.atten(machine.ADC.ATTN_11DB)
                #     pass
                # else: # Default or if not specified
                #     # adc.atten(machine.ADC.ATTN_11DB)
                #     pass # Default to 11DB for safety if not specified or invalid
                #
                # # Set ADC width (resolution) - common is 12-bit for ESP32
                # # Options: machine.ADC.WIDTH_9BIT, machine.ADC.WIDTH_10BIT,
                # #          machine.ADC.WIDTH_11BIT, machine.ADC.WIDTH_12BIT
                # # adc.width(machine.ADC.WIDTH_12BIT) # Set to 12-bit resolution (0-4095)
                #
                # config["instance"] = adc # Store the ADC object
                print(f"  {sensor_id} (ANALOG) on pin {config['pin']} initialized (placeholder). Attenuation: {config.get('attenuation', 'N/A')}")
            # Add other sensor types here
            else:
                print(f"  Warning: Unknown sensor type '{config['type']}' for sensor_id '{sensor_id}'.")
        except Exception as e:
            print(f"Error initializing sensor {sensor_id} ({config['type']}): {e}")
    print("Sensor initialization complete.")

def read_sensor_data(sensor_id, config):
    """
    Reads data from a single specified sensor.
    Args:
        sensor_id (str): The ID of the sensor to read.
        config (dict): The configuration dictionary for the sensor.
    Returns:
        dict: A dictionary containing the sensor data (e.g., {"temperature": 25.5, "humidity": 60.1})
              or None if reading fails.
    """
    instance = config.get("instance")
    if not instance:
        # This is expected if placeholder libraries are not actually imported and initialized
        # print(f"Sensor {sensor_id} not initialized. Skipping read.")
        # For now, let's return mock data if it's a known type for testing structure
        if config["type"] == "DHT22":
            return {"sensor_id": sensor_id, "type": config["type"], "temperature_celsius": 25.0, "humidity_percent": 50.0, "mock": True}
        elif config["type"] == "BMP280":
            return {"sensor_id": sensor_id, "type": config["type"], "temperature_celsius": 26.0, "pressure_hpa": 1012.5, "mock": True}
        elif config["type"] == "DS18B20":
             return {"sensor_id": sensor_id, "type": config["type"], "temperatures_celsius": {"rom_0": 27.0}, "mock": True}
        elif config["type"] == "ANALOG":
            # Mock data for an analog sensor
            mock_raw_adc = 2048 # Example raw ADC value (0-4095 for 12-bit)
            mock_voltage = (mock_raw_adc / 4095.0) * 3.3 # Example voltage calculation
            return {
                "sensor_id": sensor_id,
                "type": config["type"],
                "name": config.get("name", sensor_id),
                "adc_raw": mock_raw_adc,
                "voltage": mock_voltage,
                "mock": True
            }
        return None


    data = {"sensor_id": sensor_id, "type": config["type"]}
    try:
        if config["type"] == "DHT22":
            # Placeholder for DHT22 reading
            # instance.measure()
            # data["temperature_celsius"] = instance.temperature()
            # data["humidity_percent"] = instance.humidity()
            pass # Remove pass when actual library is used
        elif config["type"] == "BMP280":
            # Placeholder for BMP280 reading
            # data["temperature_celsius"] = instance.temperature
            # data["pressure_hpa"] = instance.pressure / 100 # Convert Pa to hPa
            pass # Remove pass when actual library is used
        elif config["type"] == "ANALOG":
            # Placeholder for Analog ADC reading
            # raw_value = instance.read() # instance here would be the adc object
            # voltage = (raw_value / 4095.0) * 3.3 # Example for 12-bit ADC & 3.3V ref with 11DB atten
            # data["adc_raw"] = raw_value
            # data["voltage"] = voltage
            # data["name"] = config.get("name", sensor_id)
            pass # Remove pass when actual library is used
        elif config["type"] == "DS18B20":
            # Placeholder for DS18B20 reading
            # if config.get("roms"):
            #    instance.convert_temp()
            #    time.sleep_ms(750) # DS18B20 conversion time
            #    temperatures = {}
            #    for i, rom in enumerate(config["roms"]):
            #        temp = instance.read_temp(rom)
            #        temperatures[f"rom_{i}"] = temp
            #    data["temperatures_celsius"] = temperatures
            # else:
            #    print(f"  No ROMs found for DS18B20 sensor {sensor_id}.")
            #    return None
            pass # Remove pass when actual library is used
        # Add other sensor types here
        else:
            print(f"  Warning: Unknown sensor type '{config['type']}' for reading sensor_id '{sensor_id}'.")
            return None
        return data
    except Exception as e:
        print(f"Error reading sensor {sensor_id} ({config['type']}): {e}")
        return None

def read_all_sensors():
    """
    Reads data from all configured and initialized sensors.
    Returns:
        list: A list of dictionaries, where each dictionary is the data from a sensor.
    """
    all_sensor_data = []
    for sensor_id, config in SENSOR_CONFIG.items():
        data = read_sensor_data(sensor_id, config)
        if data:
            all_sensor_data.append(data)
    return all_sensor_data

# -----------------------------------------------------------------------------
# Serial Communication Functions
# -----------------------------------------------------------------------------
def setup_serial():
    """Initializes UART communication."""
    global uart
    try:
        uart = machine.UART(UART_ID, UART_BAUD_RATE)
        # uart.init(UART_BAUD_RATE, bits=8, parity=None, stop=1) # For older MicroPython versions
        print(f"UART {UART_ID} initialized at {UART_BAUD_RATE} baud.")
    except Exception as e:
        print(f"Error initializing UART: {e}")

def send_serial_data(data):
    """
    Sends data (typically a JSON string) over UART.
    Args:
        data (str): The string data to send.
    """
    if uart:
        try:
            uart.write(data + '\n') # Add newline as a delimiter
            # print(f"Sent: {data}")
        except Exception as e:
            print(f"Error sending serial data: {e}")
    else:
        print("UART not initialized. Cannot send data.")

def receive_serial_data():
    """
    Checks for and processes incoming serial data.
    This could be used for commands, configuration updates, etc.
    Returns:
        dict: Parsed JSON data if a complete message is received, otherwise None.
    """
    global SENSOR_CONFIG
    if uart and uart.any():
        try:
            received_bytes = uart.readline()
            if received_bytes:
                received_str = received_bytes.decode('utf-8').strip()
                print(f"Received raw: {received_str}")
                try:
                    message = ujson.loads(received_str)
                    print(f"Parsed message: {message}")

                    if "command" in message:
                        handle_command(message)
                    elif "config" in message: # Expecting a full sensor config object
                        print("Received new sensor configuration.")
                        SENSOR_CONFIG = message["config"]
                        initialize_sensors() # Re-initialize sensors with new config
                        send_serial_data(ujson.dumps({"status": "config_updated", "new_config": SENSOR_CONFIG}))
                    return message
                except ValueError:
                    print(f"Error: Could not decode JSON from: {received_str}")
                    send_serial_data(ujson.dumps({"error": "Invalid JSON format"}))
                    return None
        except Exception as e:
            print(f"Error receiving or processing serial data: {e}")
            return None
    return None

def handle_command(message):
    """
    Handles commands received via serial.
    Args:
        message (dict): The parsed command message.
    """
    command = message.get("command")
    payload = message.get("payload", {})
    print(f"Handling command: {command} with payload: {payload}")

    if command == "STATUS_CHECK":
        status_report = {
            "status": "OK",
            "firmware_version": "1.0.0", # Example version
            "uptime_ms": time.ticks_ms(),
            "sensor_count": len(SENSOR_CONFIG),
            "configured_sensors": list(SENSOR_CONFIG.keys())
        }
        send_serial_data(ujson.dumps({"response_to": "STATUS_CHECK", "data": status_report}))
    elif command == "READ_SENSORS_NOW":
        sensor_data = read_all_sensors()
        response = {"response_to": "READ_SENSORS_NOW", "data": sensor_data}
        send_serial_data(ujson.dumps(response))
    elif command == "SET_LOOP_DELAY":
        global MAIN_LOOP_DELAY_MS
        new_delay = payload.get("delay_ms")
        if isinstance(new_delay, int) and new_delay > 0:
            MAIN_LOOP_DELAY_MS = new_delay
            print(f"Main loop delay updated to {MAIN_LOOP_DELAY_MS} ms.")
            send_serial_data(ujson.dumps({"status": "loop_delay_updated", "new_delay_ms": MAIN_LOOP_DELAY_MS}))
        else:
            send_serial_data(ujson.dumps({"error": "Invalid delay_ms for SET_LOOP_DELAY"}))
    # Add more command handlers here
    else:
        print(f"Unknown command: {command}")
        send_serial_data(ujson.dumps({"error": "Unknown command", "command_received": command}))

# -----------------------------------------------------------------------------
# Main Application Logic
# -----------------------------------------------------------------------------
def main():
    """Main function to run the firmware logic."""
    setup_serial()
    # Send a boot message or request initial configuration
    boot_message = {"status": "ESP32_BOOTED", "message": "Awaiting sensor configuration..."}
    send_serial_data(ujson.dumps(boot_message))
    print("ESP32 Booted. Awaiting sensor configuration via serial.")

    # Note: Sensor initialization will happen once a valid configuration is received.

    last_sensor_read_time = time.ticks_ms()

    while True:
        # Check for incoming serial data (non-blocking)
        received_message = receive_serial_data()
        # If a new config was received, SENSOR_CONFIG is updated and sensors re-initialized by receive_serial_data

        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_sensor_read_time) >= MAIN_LOOP_DELAY_MS:
            last_sensor_read_time = current_time

            if SENSOR_CONFIG: # Only read if sensors are configured
                print(f"{time.ticks_ms()}: Reading sensor data...")
                sensor_data_list = read_all_sensors()

                if sensor_data_list:
                    # Prepare data for sending
                    data_to_send = {
                        "timestamp_ms": time.ticks_ms(),
                        "data": sensor_data_list
                    }
                    json_output = ujson.dumps(data_to_send)
                    send_serial_data(json_output)
                else:
                    # print("No data collected from sensors in this cycle.")
                    pass # Or send an empty data message if required
            else:
                # print("No sensors configured. Waiting for configuration...")
                pass # Waiting for configuration

        # A small delay to prevent tight looping if MAIN_LOOP_DELAY_MS is large,
        # allowing serial receive to be more responsive.
        # This is especially important if MAIN_LOOP_DELAY_MS is much larger than the time
        # it takes to read sensors and process serial.
        time.sleep_ms(10)


if __name__ == "__main__":
    main()
