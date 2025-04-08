import ctypes
import time
import os
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import secrets
import base64

# Function to generate a random key using secrets
def generate_key():
    # Generate a secure 16-byte session key as a hex string using secrets
    key = secrets.token_bytes(16)  # 16-byte key (16 bytes in raw format)
    encoded_key = base64.b64encode(key).decode('utf-8')  # Base64 encode the key and return as string
    return encoded_key

# Function to log messages with timestamp (using Base64 encoded key)
def log_message(message, encoded_key):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}]  {message} | Encoded Key: {encoded_key}"  # Log with the encoded key

    # Write the log message to the file
    with open("api_monitor.log", "a") as log_file:
        log_file.write(log_message + "\n")
    
    print(f"[{timestamp}]  {message} | Encoded Key: {encoded_key}")  # Print the message to the console

# Monitor active connections using netstat
def monitor_connections(expected_encoded_key):
    try:
        result = subprocess.check_output(["netstat", "-an"], universal_newlines=True)
        connections = [line for line in result.splitlines() if 'ESTABLISHED' in line]
        
        for conn in connections:
            connection_key = secrets.token_bytes(16)  # Generate a random 16-byte key

            # Base64 encode the generated key for comparison
            encoded_connection_key = base64.b64encode(connection_key).decode('utf-8')

            if encoded_connection_key == expected_encoded_key:
                log_message(f"Connection: {conn} | Connection verified successfully.", expected_encoded_key)
            else:
                log_message(f"Connection: {conn} | Unauthorized connection detected.", expected_encoded_key)

    except subprocess.CalledProcessError as e:
        log_message(f"Error fetching connections: {e}", expected_encoded_key)

# Monitor system resource usage (CPU and Memory) for the current process
def monitor_system_resources(expected_encoded_key):
    pid = os.getpid()
    try:
        result = subprocess.check_output(f'tasklist /FI "PID eq {pid}" /FO LIST', universal_newlines=True)
        cpu_usage = None
        memory_usage = None

        for line in result.splitlines():
            if "CPU Time" in line:
                cpu_usage = line.split(":")[1].strip()
            if "Mem Usage" in line:
                memory_usage = line.split(":")[1].strip()

        log_message(f"CPU Usage: {cpu_usage}", expected_encoded_key)
        log_message(f"Memory Usage: {memory_usage}", expected_encoded_key)
    except subprocess.CalledProcessError as e:
        log_message(f"Error fetching system resources: {e}", expected_encoded_key)

# Function to load the API library and monitor it
def load_and_monitor_api(library_path, expected_encoded_key):
    try:
        # Load the library
        api_lib = ctypes.CDLL(library_path)
        api_lib.check_status.restype = ctypes.c_int

        # Start monitoring loop
        while True:
            try:
                # Call the API to check the status
                status = api_lib.check_status()

                # Monitor connections and system resources every 5 seconds
                monitor_connections(expected_encoded_key)
                monitor_system_resources(expected_encoded_key)

                # Log the API status check result
                if status == 0:
                    log_message("API status check passed.", expected_encoded_key)
                    ctypes.windll.user32.MessageBoxW(0, "API Status: Passed", "Notification", 0x40 | 0x1)  # Success notification
                else:
                    log_message(f"API status check failed with code {status}.", expected_encoded_key)
                    ctypes.windll.user32.MessageBoxW(0, f"API Status: Failed with code {status}", "Notification", 0x10 | 0x1)  # Error notification

                time.sleep(5)  # Monitor the API every 5 seconds
            except Exception as e:
                log_message(f"Error occurred: {e}", expected_encoded_key)
                break
    except OSError as e:
        log_message(f"Error loading library: {e}", expected_encoded_key)
        ctypes.windll.user32.MessageBoxW(0, f"Error loading library: {e}", "Notification", 0x10 | 0x1)  # Error notification
        exit(1)

# Tkinter Interface to get the API library path
def open_tkinter_interface():
    expected_encoded_key = generate_key()  # Generate a unique random key for this session

    def on_submit():
        library_path = library_path_entry.get()
        if library_path:
            load_and_monitor_api(library_path, expected_encoded_key)
        else:
            messagebox.showerror("Input Error", "Please enter a valid library path.")
    
    # Create the main Tkinter window
    window = tk.Tk()
    window.title("Track")
    window.geometry("400x200")
    window.configure(bg='white')

    # Add a label
    label = tk.Label(window, text="Enter the library path of the API to monitor:", bg='white', font=("Arial", 12))
    label.pack(pady=10)

    # Add an entry widget for the library path
    library_path_entry = tk.Entry(window, width=40, font=("Arial", 12))
    library_path_entry.pack(pady=5)

    # Add a submit button
    submit_button = tk.Button(window, text="Submit", command=on_submit, bg='black', fg='white', font=("Arial", 12))
    submit_button.pack(pady=20)

    # Start the Tkinter event loop
    window.mainloop()

# Start the Tkinter interface
if __name__ == "__main__":
    open_tkinter_interface()
