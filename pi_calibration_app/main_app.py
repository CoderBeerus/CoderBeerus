import customtkinter
import serial
from serial.tools import list_ports
import threading
import json
import time # Will be used for small delays or timeouts if necessary

customtkinter.set_appearance_mode("System")  # Options: "System", "Light", "Dark"
customtkinter.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

class CalibrationApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Configure main window
        self.title("ESP32 ADC Calibration Tool")
        self.geometry("1024x768") # Increased size for more content

        self.serial_connection = None
        self.listen_thread = None
        self.stop_event = None

        self.sensor_readings = {}  # Stores latest data for each sensor_id
        self.selected_sensor_id = None # Tracks which sensor's details are being viewed
        self.sensor_data_labels = {} # References to labels displaying sensor data for easy update
        self.sensor_data_display_frame = None # Frame within main_content_frame for specific sensor data
        self.calibration_status_label = None # Label to show calibration status
        self.cal_settings_window = None # For the calibration settings top-level window
        self.standards_textbox = None # Textbox in the settings window
        self.cal_settings_status_label = None # Status label in settings window

        self.calibration_standards = None # Will hold loaded calibration standards
        self._load_calibration_standards()

        # Define the sensor configuration to be sent to ESP32
        # The ESP32 firmware's `receive_serial_data` expects `message["config"]`
        # So, the structure here is what will be under the "config" key in the JSON sent.
        self.esp32_sensor_config_payload = {
            "dp_sensor_1": {"type": "ANALOG", "pin": 32, "name": "DP Transmitter Alpha", "attenuation": "11DB"},
            "temp_sensor_office": {"type": "DHT22", "pin": 4, "name": "Office Temperature"},
            "analog_generic_1": {"type": "ANALOG", "pin": 33, "name": "Generic Analog Input 1", "attenuation": "11DB"},
            "analog_generic_2": {"type": "ANALOG", "pin": 34, "name": "Generic Analog Input 2", "attenuation": "6DB"},
        }

        self._setup_ui()
        self._populate_serial_ports()

    def _setup_ui(self):
        # Configure grid layout for the main window
        self.grid_columnconfigure(1, weight=1) # Main content area will expand
        self.grid_rowconfigure(1, weight=1)    # Sensor list and main content will expand

        # --- Top Connection Frame ---
        self.connection_frame = customtkinter.CTkFrame(self, height=50)
        self.connection_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew") # pady adjusted

        self.serial_label = customtkinter.CTkLabel(self.connection_frame, text="Serial Port:")
        self.serial_label.pack(side="left", padx=(10, 5), pady=10)

        self.serial_port_menu = customtkinter.CTkOptionMenu(self.connection_frame, values=["No Ports Found"])
        self.serial_port_menu.pack(side="left", padx=5, pady=10)

        self.connect_button = customtkinter.CTkButton(self.connection_frame, text="Connect", command=self._connect_esp32)
        self.connect_button.pack(side="left", padx=5, pady=10)

        self.cal_settings_button = customtkinter.CTkButton(self.connection_frame, text="Calibration Settings", command=self._open_calibration_settings_window)
        self.cal_settings_button.pack(side="left", padx=5, pady=10)

        self.status_label = customtkinter.CTkLabel(self.connection_frame, text="Status: Disconnected", text_color="orange") # Initial color set
        self.status_label.pack(side="left", padx=(10,5), pady=10) # padx adjusted


        # --- Left Panel Frame (Container for Sensor List) ---
        self.left_panel_frame = customtkinter.CTkFrame(self, width=250)
        self.left_panel_frame.grid(row=1, column=0, padx=(10,5), pady=(5,10), sticky="nswe") # pady adjusted
        self.left_panel_frame.grid_rowconfigure(1, weight=1) # Make scroll frame expand

        self.sensor_list_label = customtkinter.CTkLabel(self.left_panel_frame, text="Available Sensors", font=customtkinter.CTkFont(size=14, weight="bold")) # Font verified
        self.sensor_list_label.grid(row=0, column=0, padx=10, pady=(5,10), sticky="ew") # pady adjusted

        self.sensor_scroll_frame = customtkinter.CTkScrollableFrame(self.left_panel_frame)
        self.sensor_scroll_frame.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nswe") # pady adjusted

        self.sensor_placeholder_label = customtkinter.CTkLabel(self.sensor_scroll_frame, text="Connect to ESP32\nto see sensors.")
        # self.sensor_placeholder_label.pack(pady=20, padx=10) # Initially packed by _update_sensor_list_ui

        # --- Main Content Frame (Right of Sensor List) ---
        self.main_content_frame = customtkinter.CTkFrame(self)
        self.main_content_frame.grid(row=1, column=1, padx=(5,10), pady=(5,10), sticky="nswe") # pady adjusted

        self.main_content_placeholder_label = customtkinter.CTkLabel(
            self.main_content_frame,
            text="Select a sensor from the left panel to view its data.",
            font=customtkinter.CTkFont(size=16)
        )
        self.main_content_placeholder_label.pack(pady=20, padx=20, fill="both", expand=True) # fill and expand

    def _populate_serial_ports(self):
        ports = list_ports.comports()
        if ports:
            port_names = [port.device for port in ports]
            self.serial_port_menu.configure(values=port_names)
            self.serial_port_menu.set(port_names[0]) # Select the first available port
        else:
            self.serial_port_menu.configure(values=["No Ports Found"])
            self.serial_port_menu.set("No Ports Found")
        self._update_sensor_list_ui(clear=True) # Ensure sensor list is cleared/placeholder shown initially


    def _connect_esp32(self):
        selected_port = self.serial_port_menu.get()
        if selected_port == "No Ports Found" or not selected_port:
            self.status_label.configure(text="Status: Error - No port selected", text_color="red")
            print("Connection failed: No port selected.")
            return

        if self.serial_connection: # Already connected
            print("Already connected. Please disconnect first.")
            self.status_label.configure(text="Status: Already connected. Disconnect first.", text_color="orange")
            return

        try:
            self.status_label.configure(text=f"Status: Connecting to {selected_port}...", text_color="blue") # Theme default blue
            self.update_idletasks() # Force UI update

            self.serial_connection = serial.Serial(selected_port, baudrate=115200, timeout=1)
            print(f"Serial port {selected_port} opened.")

            # Send configuration to ESP32
            config_to_send = {"config": self.esp32_sensor_config_payload}
            config_message = json.dumps(config_to_send)
            self.serial_connection.write(config_message.encode('utf-8') + b'\n')
            print(f"Sent configuration: {config_message}")

            # Wait for a moment for ESP32 to process config and respond (optional)
            # time.sleep(0.5) # Adjust as needed, or implement handshake

            self.connect_button.configure(text="Disconnect", command=self._disconnect_esp32)
            self.status_label.configure(text=f"Status: Connected to {selected_port}", text_color="green")
            print(f"Successfully connected to {selected_port}.")

            self._start_listening()
            self._update_sensor_list_ui()

        except serial.SerialException as e:
            self.serial_connection = None # Ensure it's None on failure
            self.status_label.configure(text=f"Status: Error - {e}", text_color="red")
            print(f"Failed to connect to {selected_port}: {e}")
        except Exception as e: # Catch other unexpected errors
            self.serial_connection = None
            self.status_label.configure(text=f"Status: Error - {str(e)}", text_color="red")
            print(f"An unexpected error occurred: {e}")

    def _disconnect_esp32(self):
        print("Attempting to disconnect...")
        self._stop_listening() # Signal the listening thread to stop

        if self.serial_connection:
            try:
                if self.serial_connection.is_open:
                    self.serial_connection.close()
                print("Serial port closed.")
            except Exception as e:
                print(f"Error closing serial port: {e}")
            finally:
                self.serial_connection = None

        self.status_label.configure(text="Status: Disconnected", text_color="orange")
        self.connect_button.configure(text="Connect", command=self._connect_esp32)
        self._update_sensor_list_ui(clear=True)
        print("Successfully disconnected.")

    def _update_sensor_list_ui(self, clear=False):
        # Clear existing widgets from the scroll frame
        for widget in self.sensor_scroll_frame.winfo_children():
            widget.destroy()

        if clear or not self.esp32_sensor_config_payload or not self.serial_connection:
            self.sensor_placeholder_label = customtkinter.CTkLabel(self.sensor_scroll_frame, text="Connect to ESP32\nto see sensors.")
            self.sensor_placeholder_label.pack(pady=20, padx=10)
            return

        if not self.esp32_sensor_config_payload.get("dp_sensor_1"): # A bit of a hack to check if it's default
             #This check might need to be more robust if esp32_sensor_config_payload can be empty but valid
            self.sensor_placeholder_label = customtkinter.CTkLabel(self.sensor_scroll_frame, text="No sensors configured\nor config not sent.")
            self.sensor_placeholder_label.pack(pady=20, padx=10)
            return


        for sensor_id, config in self.esp32_sensor_config_payload.items():
            sensor_name = config.get("name", sensor_id)
            btn = customtkinter.CTkButton(
                self.sensor_scroll_frame,
                text=sensor_name,
                command=lambda sid=sensor_id: self._select_sensor(sid)
            )
            btn.pack(pady=5, padx=10, fill="x")

    def _select_sensor(self, sensor_id):
        self.selected_sensor_id = sensor_id
        print(f"Sensor selected: {sensor_id}")

        # Destroy placeholder if it exists
        if self.main_content_placeholder_label:
            self.main_content_placeholder_label.destroy()
            self.main_content_placeholder_label = None # Ensure it's gone

        # Clear and recreate the sensor_data_display_frame
        if self.sensor_data_display_frame:
            self.sensor_data_display_frame.destroy()

        self.sensor_data_display_frame = customtkinter.CTkFrame(self.main_content_frame)
        self.sensor_data_display_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.sensor_data_display_frame.grid_columnconfigure(0, weight=1) # Allow labels to align

        selected_sensor_name = self.esp32_sensor_config_payload.get(sensor_id, {}).get("name", sensor_id)
        live_data_title_label = customtkinter.CTkLabel( # Renamed for clarity
            self.sensor_data_display_frame,
            text=f"Live Data for: {selected_sensor_name}",
            font=customtkinter.CTkFont(size=16, weight="bold") # Font verified
        )
        live_data_title_label.pack(pady=(5,10), padx=10, anchor="w")

        self.sensor_data_labels = {} # Reset labels for the new sensor view

        # Create a dedicated frame for actual data labels to manage their packing order
        # This frame will be packed before the calibration section title.
        self.actual_data_frame = customtkinter.CTkFrame(self.sensor_data_display_frame, fg_color="transparent")
        self.actual_data_frame.pack(fill="x", padx=0, pady=0, anchor="w") # Use padx=0 here, inner labels will have it.

        # Calibration Details Section
        calibration_title_label = customtkinter.CTkLabel(
            self.sensor_data_display_frame,
            text="Calibration Details",
            font=customtkinter.CTkFont(size=16, weight="bold") # Font for section title
        )
        calibration_title_label.pack(pady=(15,5), padx=10, anchor="w") # pady adjusted

        self.calibration_status_label = customtkinter.CTkLabel(
            self.sensor_data_display_frame,
            text="Calibration Status: Unknown", # Initial text
            font=customtkinter.CTkFont(size=14) # Font verified
        )
        self.calibration_status_label.pack(pady=(0,10), padx=10, anchor="w")

        if self.sensor_readings.get(sensor_id):
            self._update_displayed_sensor_data(sensor_id)
        else:
            # This placeholder will be managed within _update_displayed_sensor_data
            self._update_displayed_sensor_data(sensor_id) # Call to handle placeholder logic
            self._perform_calibration_check(sensor_id)


    def _update_displayed_sensor_data(self, sensor_id):
        if sensor_id != self.selected_sensor_id or not self.sensor_data_display_frame:
            return # Not the currently selected sensor or frame doesn't exist

        data = self.sensor_readings.get(sensor_id)
        if not data:
            # This case might be handled by _select_sensor initially,
            # but if data becomes unavailable later, this could be useful.
            # Clear existing data labels first (excluding placeholders handled below)
            for key, label_widget in list(self.sensor_data_labels.items()): # list() for safe iteration
                if not key.startswith("_placeholder_"): # Underscore prefix for placeholders
                    label_widget.destroy()
                    del self.sensor_data_labels[key]

            # Ensure actual_data_frame exists, if not, something is wrong with _select_sensor
            if not hasattr(self, 'actual_data_frame') or not self.actual_data_frame.winfo_exists():
                 # Fallback or error, though _select_sensor should always create it
                error_label = customtkinter.CTkLabel(self.sensor_data_display_frame, text="UI Error: Data frame missing.")
                error_label.pack(pady=5, padx=10, anchor="w")
                self.sensor_data_labels["_placeholder_error"] = error_label
                self._perform_calibration_check(sensor_id)
                return

            if "_placeholder_data_status" in self.sensor_data_labels: # Remove old data status placeholder
                 self.sensor_data_labels["_placeholder_data_status"].destroy()
                 del self.sensor_data_labels["_placeholder_data_status"]

            no_data_text = "Waiting for data..." if not self.sensor_readings.get(sensor_id) else "No displayable data for this sensor."
            placeholder_data_label = customtkinter.CTkLabel(self.actual_data_frame, text=no_data_text)
            placeholder_data_label.pack(pady=5, padx=10, anchor="w") # padx is 10 here for content within actual_data_frame
            self.sensor_data_labels["_placeholder_data_status"] = placeholder_data_label

            self._perform_calibration_check(sensor_id) # Update calibration status based on no data
            return

        # If a placeholder like "Waiting for data..." or "No data yet" exists, remove it
        if "_placeholder_data_status" in self.sensor_data_labels:
            self.sensor_data_labels["_placeholder_data_status"].destroy()
            del self.sensor_data_labels["_placeholder_data_status"]

        # Iterate through sensor readings and create/update labels
        sorted_data_items = sorted(data.items()) # Sort for consistent display order

        for key, value in sorted_data_items:
            display_key = key.replace('_', ' ').title()
            text_to_display = f"{display_key}: {value}"

            if key not in self.sensor_data_labels:
                new_label = customtkinter.CTkLabel(
                    self.actual_data_frame, # Add to the dedicated frame for data
                    text=text_to_display,
                    font=customtkinter.CTkFont(size=12)
                )
                new_label.pack(pady=2, padx=10, anchor="w") # padx is 10 for content within actual_data_frame
                self.sensor_data_labels[key] = new_label
            else:
                self.sensor_data_labels[key].configure(text=text_to_display)

        self._perform_calibration_check(sensor_id)

    def _load_calibration_standards(self):
        try:
            with open("pi_calibration_app/calibration_standards.json", "r") as f:
                self.calibration_standards = json.load(f)
            print("Calibration standards loaded successfully.")
        except FileNotFoundError:
            print("Warning: calibration_standards.json not found.")
            self.calibration_standards = {} # Use empty dict to prevent errors later
        except json.JSONDecodeError:
            print("Error: Could not decode calibration_standards.json.")
            self.calibration_standards = {} # Use empty dict

    def _perform_calibration_check(self, sensor_id):
        if not self.calibration_status_label: # Label might not be created yet if no sensor selected
            return

        if not self.calibration_standards or not self.calibration_standards.get("sensor_types"):
            self.calibration_status_label.configure(text="Calibration Status: Standards not loaded or invalid.")
            return

        sensor_type_key = self.calibration_standards.get("sensor_instance_to_type_mapping", {}).get(sensor_id)
        if not sensor_type_key:
            self.calibration_status_label.configure(text="Calibration Status: No calibration type defined for this sensor.")
            return

        standard = self.calibration_standards.get("sensor_types", {}).get(sensor_type_key)
        if not standard:
            self.calibration_status_label.configure(text=f"Calibration Status: Standard for type '{sensor_type_key}' not found.")
            return

        value_key = standard.get("value_key")
        live_reading_obj = self.sensor_readings.get(sensor_id, {})
        live_data_point_raw = live_reading_obj.get(value_key)

        if value_key is None or live_data_point_raw is None:
            self.calibration_status_label.configure(text=f"Calibration Status: Data key '{value_key}' not found in sensor readings.")
            return

        try:
            live_data_point = float(live_data_point_raw)
        except (ValueError, TypeError):
            self.calibration_status_label.configure(text=f"Calibration Status: Sensor value '{live_data_point_raw}' is not a valid number.")
            return

        reference_points = standard.get("reference_points", [])
        if not reference_points:
            self.calibration_status_label.configure(text="Calibration Status: No reference points in standard.")
            return

        check_strategy = standard.get("check_strategy", "first_point") # Default to first_point
        target_ref_point = None
        status_text = "Error"

        if check_strategy == "first_point":
            if reference_points:
                target_ref_point = reference_points[0]
        elif check_strategy == "closest_point":
            if not reference_points:
                self.calibration_status_label.configure(text="Calibration Status: No reference points for closest_point strategy.")
                return
            # Find the reference point with the expected_value closest to live_data_point
            target_ref_point = min(reference_points, key=lambda p: abs(p.get("expected_value", float('inf')) - live_data_point))
        else:
            self.calibration_status_label.configure(text=f"Calibration Status: Unknown check strategy '{check_strategy}'.")
            return

        if not target_ref_point or "expected_value" not in target_ref_point or "tolerance_absolute" not in target_ref_point:
            self.calibration_status_label.configure(text="Calibration Status: Invalid reference point data.")
            return

        expected = float(target_ref_point["expected_value"])
        tolerance = float(target_ref_point["tolerance_absolute"])
        ref_point_name = target_ref_point.get("name", "Unnamed Point")
        unit = standard.get("unit", "")

        if abs(live_data_point - expected) <= tolerance:
            status_text = f"Within Tolerance (Expected: {expected:.2f} {unit}, Actual: {live_data_point:.2f} {unit})"
        elif live_data_point > expected:
            status_text = f"Out of Tolerance - Too High (Expected: {expected:.2f} {unit}, Actual: {live_data_point:.2f} {unit})"
        else: # live_data_point < expected
            status_text = f"Out of Tolerance - Too Low (Expected: {expected:.2f} {unit}, Actual: {live_data_point:.2f} {unit})"

        self.calibration_status_label.configure(text=f"Calibration ({ref_point_name}): {status_text}")

    def _open_calibration_settings_window(self):
        if self.cal_settings_window is not None and self.cal_settings_window.winfo_exists():
            self.cal_settings_window.focus()
            return

        self.cal_settings_window = customtkinter.CTkToplevel(self)
        self.cal_settings_window.title("Calibration Standards Settings")
        self.cal_settings_window.geometry("700x550")
        self.cal_settings_window.protocol("WM_DELETE_WINDOW", self._on_cal_settings_close)
        # self.cal_settings_window.attributes("-topmost", True) # Commented out: Can be annoying, user can bring to front

        # Configure grid
        self.cal_settings_window.grid_columnconfigure(0, weight=1)
        self.cal_settings_window.grid_rowconfigure(1, weight=1) # Textbox row

        top_label = customtkinter.CTkLabel(self.cal_settings_window, text="Edit Calibration Standards (JSON format)", font=customtkinter.CTkFont(size=14, weight="bold")) # Font verified
        top_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.standards_textbox = customtkinter.CTkTextbox(self.cal_settings_window, wrap="word")
        self.standards_textbox.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew") # pady adjusted
        try:
            self.standards_textbox.insert("1.0", json.dumps(self.calibration_standards, indent=2))
        except Exception as e:
            self.standards_textbox.insert("1.0", f"Error loading standards: {e}")
            print(f"Error populating textbox with standards: {e}")

        button_frame = customtkinter.CTkFrame(self.cal_settings_window)
        button_frame.grid(row=2, column=0, padx=10, pady=(5,10), sticky="ew") # pady adjusted

        save_button = customtkinter.CTkButton(button_frame, text="Save Standards", command=self._save_standards_from_textbox)
        save_button.pack(side="left", padx=5, pady=5)

        reload_button = customtkinter.CTkButton(button_frame, text="Reload From File", command=self._reload_standards_from_file)
        reload_button.pack(side="left", padx=5, pady=5)

        close_button = customtkinter.CTkButton(button_frame, text="Close", command=self._on_cal_settings_close)
        close_button.pack(side="right", padx=5, pady=5)

        self.cal_settings_status_label = customtkinter.CTkLabel(self.cal_settings_window, text="", font=customtkinter.CTkFont(size=12))
        self.cal_settings_status_label.grid(row=3, column=0, padx=10, pady=(0,5), sticky="ew") # pady adjusted


    def _on_cal_settings_close(self):
        if self.cal_settings_window:
            self.cal_settings_window.destroy()
        self.cal_settings_window = None
        self.standards_textbox = None # Clear reference
        self.cal_settings_status_label = None

    def _save_standards_from_textbox(self):
        if not self.standards_textbox or not self.cal_settings_status_label:
            print("Settings window components not available.")
            return

        textbox_content = self.standards_textbox.get("1.0", "end")
        try:
            new_standards = json.loads(textbox_content)
        except json.JSONDecodeError as e:
            self.cal_settings_status_label.configure(text=f"Error: Invalid JSON - {e}", text_color="red")
            return
        except Exception as e: # Other potential errors from get() or loads()
            self.cal_settings_status_label.configure(text=f"Error parsing content: {e}", text_color="red")
            return

        try:
            with open("pi_calibration_app/calibration_standards.json", "w") as f:
                json.dump(new_standards, f, indent=2)
            self.calibration_standards = new_standards # Update in-memory standards
            self.cal_settings_status_label.configure(text="Success: Standards saved to file and reloaded.", text_color="green")
            print("Calibration standards saved successfully.")
            # Optionally, re-check calibration for the current sensor
            if self.selected_sensor_id and self.serial_connection:
                self._perform_calibration_check(self.selected_sensor_id)
        except IOError as e:
            self.cal_settings_status_label.configure(text=f"Error: Could not write to file - {e}", text_color="red")
        except Exception as e:
            self.cal_settings_status_label.configure(text=f"An unexpected error occurred during save: {e}", text_color="red")


    def _reload_standards_from_file(self):
        if not self.standards_textbox or not self.cal_settings_status_label:
            print("Settings window components not available.")
            return

        self._load_calibration_standards() # This updates self.calibration_standards
        try:
            self.standards_textbox.delete("1.0", "end")
            self.standards_textbox.insert("1.0", json.dumps(self.calibration_standards, indent=2))
            self.cal_settings_status_label.configure(text="Success: Standards reloaded from file.", text_color="green")
            print("Calibration standards reloaded from file and textbox updated.")
            # Optionally, re-check calibration for the current sensor
            if self.selected_sensor_id and self.serial_connection:
                self._perform_calibration_check(self.selected_sensor_id)
        except Exception as e:
            self.cal_settings_status_label.configure(text=f"Error updating textbox: {e}", text_color="red")
            self.standards_textbox.delete("1.0", "end")
            self.standards_textbox.insert("1.0", f"Error displaying standards: {e}")
        # Ensure color is set for success on reload too
        if "Success" in self.cal_settings_status_label.cget("text"): # Check if text contains "Success"
             self.cal_settings_status_label.configure(text_color="green")


    def _start_listening(self):
        if self.listen_thread and self.listen_thread.is_alive():
            print("Listener thread already running.")
            return

        self.stop_event = threading.Event()
        self.listen_thread = threading.Thread(target=self._listen_to_esp32, daemon=True)
        self.listen_thread.start()
        print("Started listener thread for ESP32 messages.")

    def _listen_to_esp32(self):
        print("Listener thread waiting for data...")
        while not self.stop_event.is_set():
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    if self.serial_connection.in_waiting > 0:
                        raw_data_str = self.serial_connection.readline().decode('utf-8').strip()
                        if raw_data_str:
                            # IMPORTANT: Schedule UI updates from the main thread
                            self.after(0, self._handle_received_data, raw_data_str)
                        else:
                            # readline() can return empty string if timeout occurs without newline
                            time.sleep(0.01) # Small sleep to prevent busy-looping on timeout
                    else:
                        time.sleep(0.05) # Wait a bit if no data is available
                except serial.SerialException as e:
                    print(f"Serial error in listener thread: {e}")
                    self.after(0, self._handle_serial_error) # Schedule GUI update for error
                    break # Exit thread on serial error
                except UnicodeDecodeError:
                    # This can happen if the ESP32 sends non-UTF-8 data or if serial line has noise
                    print(f"UnicodeDecodeError in listener: Received non-UTF-8 data. Skipping line.")
                except Exception as e:
                    print(f"Error in listener thread: {e}") # General errors
                    time.sleep(0.1) # Avoid rapid looping on other errors
            else:
                # Connection closed or not established
                print("Listener thread: Serial connection not available. Stopping.")
                break
        print("Listener thread stopped.")

    def _handle_received_data(self, raw_data_str):
        """Handles data received from ESP32. Called by self.after() from listener thread."""
        # print(f"ESP32_RX_RAW: {raw_data_str}") # Keep for debugging if needed
        try:
            data_packet = json.loads(raw_data_str)
            # print(f"ESP32_RX_JSON: {data_packet}") # For debugging parsed JSON

            if "data" in data_packet and isinstance(data_packet["data"], list):
                for item in data_packet["data"]:
                    sensor_id = item.get("sensor_id")
                    if sensor_id:
                        self.sensor_readings[sensor_id] = item
                        if sensor_id == self.selected_sensor_id:
                            self._update_displayed_sensor_data(sensor_id)
                    else:
                        print(f"Warning: Received data item without sensor_id: {item}")
            elif "status" in data_packet: # Handle status messages from ESP32 firmware
                print(f"ESP32 Status: {data_packet}")
                if data_packet.get("status") == "config_updated":
                     self.status_label.configure(text="Status: ESP32 confirmed config update", text_color="green")
                # Add more status handling as needed
            elif "error" in data_packet:
                print(f"ESP32 Error: {data_packet.get('error')}")
                self.status_label.configure(text=f"Status: ESP32 Error - {data_packet.get('error')}", text_color="red")
            else:
                print(f"ESP32_RX (Unknown JSON format): {raw_data_str}")

        except json.JSONDecodeError:
            print(f"ESP32_RX (Non-JSON): {raw_data_str}")
        except Exception as e:
            print(f"Error processing received data: {e}")


    def _handle_serial_error(self):
        """Handles serial errors that occur in the listener thread, updating UI."""
        if self.serial_connection: # Check if we weren't already in a disconnect process
            print("Serial communication error. Attempting to disconnect.")
            # _disconnect_esp32() will be called, which updates the status label color
            self._disconnect_esp32()
            self.status_label.configure(text="Status: Error - Serial connection lost", text_color="red")


    def _stop_listening(self):
        if self.stop_event:
            self.stop_event.set()
            print("Stop event set for listener thread.")
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1) # Wait for the thread to finish
            if self.listen_thread.is_alive():
                print("Listener thread did not stop in time.")
        self.listen_thread = None
        self.stop_event = None # Clear the event for next connection

    def on_closing(self):
        """Called when the application window is closed."""
        print("Application closing...")
        self._disconnect_esp32() # Ensure clean disconnection
        self.destroy()


if __name__ == "__main__":
    app = CalibrationApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing) # Handle window close button
    app.mainloop()
