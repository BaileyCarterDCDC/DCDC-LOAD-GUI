import tkinter as tk
import serial
import threading

class SerialController:
    def __init__(self, port, baudrate):
        self.serial_port = port
        self.serial_baudrate = baudrate
        self.serial_connection = None
        self.receive_thread = None
        self.receive_callback = None
        self.last_command = ""
        self.incoming_data = ""
        self.resistance_values = [0] * 12
        self.total_resistance = 0
    
    def connect(self):
        try:
            self.serial_connection = serial.Serial(self.serial_port, self.serial_baudrate)
            print("Connected to Arduino on port", self.serial_port)
            self.start_receive_thread()
        except serial.SerialException as e:
            error_message = f"Failed to connect to Arduino: {e}"
            print(error_message)
            if self.receive_callback:
                self.receive_callback(error_message)
    
    def start_receive_thread(self):
        self.receive_thread = threading.Thread(target=self.receive_data)
        self.receive_thread.daemon = True
        self.receive_thread.start()
    
    def receive_data(self):
        while True:
            if self.serial_connection:
                data = self.serial_connection.readline().decode().strip()
                if data:
                    self.incoming_data = data
                    if self.receive_callback:
                        self.receive_callback(data)
    
    def send_command(self, command):
        if self.serial_connection:
            self.serial_connection.write(command.encode())
            print("Sent command:", command)
            self.last_command = command
        else:
            print("Serial connection not established. Cannot send command.")

class App:
    def __init__(self, master):
        self.master = master
        self.master.title("Relay load bank")
        self.master.geometry("1650x700")
        self.master.configure(bg="#333333")  # Dark theme background color

        self.serial_controller = SerialController(port='com7', baudrate=57600)
        self.serial_controller.connect()

        # Define the commands for each button and corresponding resistance values
        self.button_commands = {
            "Relay 1\n 0.48 hm": ("toggle 1\n", 0.48),
            "Relay 2\n 0.48 hm": ("toggle 2\n", 0.48),
            "Relay 3\n 0.48 hm": ("toggle 3\n", 0.48),
            "Relay 4\n 0.48 hm": ("toggle 4\n", 0.48),
            "Relay 5\n 0.48 hm": ("toggle 5\n", 0.48),
            "Relay 6\n 0.48 hm": ("toggle 6\n", 0.48),
            "Relay 7\n add": ("toggle 7\n", 0.48),
            "Relay 8\n add": ("toggle 8\n", 0.48),
            "Relay 9\n add": ("toggle 9\n", 0.48),
            "Relay 10\n add": ("toggle 10\n", 0.48)
        }

        # Initialize button colors as red
        self.button_colors = ["red"] * len(self.button_commands)

        # Create buttons for each command, arranged in two rows
        self.buttons = []
        for i, (button_label, _) in enumerate(self.button_commands.items()):
            row = i // 6  # Determine row based on button index
            col = i % 6   # Determine column based on button index

            button = tk.Button(master, text=button_label, bg="red", fg="white", activebackground="green",
                                activeforeground="white", font=("Arial", 12), bd=0, padx=10, pady=5,
                                command=lambda idx=i: self.toggle_button(idx))
            button.grid(row=row, column=col, padx=10, pady=5)
            self.buttons.append(button)

        # Create a frame for incoming messages
        self.incoming_frame = tk.Frame(master, bg="#222222", bd=2)
        self.incoming_frame.grid(row=2, column=0, columnspan=6, padx=10, pady=5, sticky="nsew")

        self.incoming_label = tk.Label(self.incoming_frame, text="Incoming Messages", bg="#222222", fg="white", font=("Arial", 12))
        self.incoming_label.pack(pady=(10, 5))

        self.incoming_text = tk.Text(self.incoming_frame, bg="#333333", fg="white", font=("Arial", 10), height=5, bd=0)
        self.incoming_text.pack(fill="both", padx=10, pady=(0, 10))
        self.incoming_text.config(state="disabled")

        # Create a frame for outgoing messages
        self.outgoing_frame = tk.Frame(master, bg="#222222", bd=2)
        self.outgoing_frame.grid(row=3, column=0, columnspan=6, padx=10, pady=5, sticky="nsew")

        self.outgoing_label = tk.Label(self.outgoing_frame, text="Outgoing Messages", bg="#222222", fg="white", font=("Arial", 12))
        self.outgoing_label.pack(pady=(10, 5))

        self.outgoing_text = tk.Text(self.outgoing_frame, bg="#333333", fg="white", font=("Arial", 10), height=5, bd=0)
        self.outgoing_text.pack(fill="both", padx=10, pady=(0, 10))
        self.outgoing_text.config(state="disabled")

        self.serial_controller.receive_callback = self.update_incoming_messages

        # Create a frame for current display
        self.current_frame = tk.Frame(master, bg="#222222", bd=2)
        self.current_frame.grid(row=0, column=6, rowspan=4, padx=10, pady=5, sticky="nsew")

        self.current_label = tk.Label(self.current_frame, text="Current (A)", bg="#222222", fg="white", font=("Arial", 12))
        self.current_label.pack(pady=(10, 5))

        self.current_value = tk.Label(self.current_frame, text="", bg="#333333", fg="green", font=("Arial", 24), bd=0)
        self.current_value.pack(fill="both", padx=10, pady=(0, 10))
        
        self.update_total_current()

        self.total_resistance_label = tk.Label(self.current_frame, text="Total Resistance (Ohms)", bg="#222222", fg="white", font=("Arial", 12))
        self.total_resistance_label.pack(pady=(10, 5))

        self.total_resistance_value = tk.Label(self.current_frame, text="", bg="#333333", fg="green", font=("Arial", 24), bd=0)
        self.total_resistance_value.pack(fill="both", padx=10, pady=(0, 10))
        
        self.update_total_resistance()

        # Create a frame for manual command entry
        self.manual_command_frame = tk.Frame(master, bg="#222222", bd=2)
        self.manual_command_frame.grid(row=4, column=0, columnspan=6, padx=10, pady=5, sticky="nsew")

        self.manual_command_label = tk.Label(self.manual_command_frame, text="Enter Manual Command:", bg="#222222", fg="white", font=("Arial", 12))
        self.manual_command_label.pack(pady=(10, 5))

        self.manual_command_entry = tk.Entry(self.manual_command_frame, bg="#333333", fg="white", font=("Arial", 10), bd=0)
        self.manual_command_entry.pack(fill="x", padx=10, pady=(0, 10))

        self.send_manual_command_button = tk.Button(self.manual_command_frame, text="Send", bg="#007BFF", fg="white", font=("Arial", 12),
                                                    bd=0, padx=10, pady=5, command=self.send_manual_command)
        self.send_manual_command_button.pack(pady=(0, 10))

    def toggle_button(self, idx):
        current_color = self.button_colors[idx]
        if current_color == "red":
            new_color = "green"
        else:
            new_color = "red"

        self.buttons[idx].configure(bg=new_color)
        self.button_colors[idx] = new_color  # Update button color in the list

        # Send corresponding command to Arduino
        button_label, (command, resistance) = list(self.button_commands.items())[idx]
        self.serial_controller.send_command(command)

        # Update outgoing messages box with the last command sent
        self.outgoing_text.config(state="normal")
        self.outgoing_text.insert("end", command + "\n")
        self.outgoing_text.see("end")
        self.outgoing_text.config(state="disabled")

        # Update total resistance based on button state
        if (self.serial_controller.total_resistance == 0.48) and current_color == "green":
                self.serial_controller.total_resistance = 0
        else:
                if self.serial_controller.total_resistance == 0:
                    self.serial_controller.total_resistance +=  resistance
                else:
                    # Update total resistance and current
                    if current_color == "red":
                        self.serial_controller.total_resistance= 1/(1/(self.serial_controller.total_resistance) + 1/(resistance))
                    else:
                        self.serial_controller.total_resistance= 1/(1/(self.serial_controller.total_resistance) - 1/(resistance))
        if (self.serial_controller.total_resistance <= 0.01):
                self.serial_controller.total_resistance = 0
        self.update_total_resistance()

    def update_incoming_messages(self, message):
        self.incoming_text.config(state="normal")
        self.incoming_text.insert("end", message + "\n")
        self.incoming_text.see("end")
        self.incoming_text.config(state="disabled")

    def update_total_resistance(self):
        self.total_resistance_value.config(text=str(round(self.serial_controller.total_resistance,3)))
        self.update_total_current()

    def update_total_current(self):
        voltage = 14.5  # Volts
        total_resistance = self.serial_controller.total_resistance
        if total_resistance != 0:
            total_current = voltage / total_resistance
        else:
            total_current = 0
        self.current_value.config(text=str(round((total_current),2)))

    def send_manual_command(self):
        command = self.manual_command_entry.get()
        self.serial_controller.send_command(command)

        # Update outgoing messages box with the manual command sent
        self.outgoing_text.config(state="normal")
        self.outgoing_text.insert("end", command + "\n")
        self.outgoing_text.see("end")
        self.outgoing_text.config(state="disabled")
        self.manual_command_entry.delete(0, 'end')

# Create the main application window
root = tk.Tk()
app = App(root)
root.mainloop()
