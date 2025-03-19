import tkinter as tk
from tkinter import messagebox
import threading
import queue
from typing import Dict, Any, Optional, List

# Import backend functions
from backend.optimization import curvefit_optimize
from backend.netlist_parse import parse_netlist, Component

# Import frontend windows.
from .netlist_uploader import NetlistUploaderWindow
from .parameter_selection import ParameterSelectionWindow
from .optimization_settings.optimization_settings_window import (
    OptimizationSettingsWindow,
)

# --- Message Types ---
# Use constants for message types to avoid typos and improve readability.
MSG_START_OPTIMIZATION = "START_OPTIMIZATION"
MSG_OPTIMIZATION_COMPLETE = "OPTIMIZATION_COMPLETE"
MSG_OPTIMIZATION_ERROR = "OPTIMIZATION_ERROR"
MSG_PROGRESS_UPDATE = "PROGRESS_UPDATE"  # Added for progress updates


class AppController:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Circuit Optimizer")
        self.root.geometry("800x600")
        self.current_window: Optional[tk.Frame] = None
        self.app_data: Dict[str, Any] = {
            "netlist_path": None,
            "selected_parameters": [],  # This is now ONLY for UI display
            "optimization_settings": {},
        }
        self.optimization_thread: Optional[threading.Thread] = None
        self.message_queue = queue.Queue()  # Queue for communication
        self.show_netlist_uploader()

    def show_netlist_uploader(self):
        self._show_window(NetlistUploaderWindow)

    def show_parameter_selection(self):
        self._show_window(ParameterSelectionWindow)

    def show_optimization_settings(self):
        self._show_window(OptimizationSettingsWindow)

    def _show_window(self, window_class: type[tk.Frame], **kwargs):
        if self.current_window:
            self.current_window.destroy()
        self.current_window = window_class(self.root, self, **kwargs)
        self.current_window.pack(fill=tk.BOTH, expand=True)

    def navigate(self, target_window_name: str):
        if target_window_name == "parameter_selection":
            self.show_parameter_selection()
        elif target_window_name == "netlist_uploader":
            self.show_netlist_uploader()
        elif target_window_name == "optimization_settings":
            self.show_optimization_settings()

    def update_app_data(self, key: str, value: Any):
        self.app_data[key] = value

    def get_app_data(self, key: str) -> Any:
        return self.app_data.get(key)

    def start_optimization(self):
        """Starts the optimization process in a separate thread."""

        if self.optimization_thread and self.optimization_thread.is_alive():
            messagebox.showwarning("Warning", "Optimization already in progress.")
            return

        # --- 1. Get all necessary data from app_data ---
        netlist_path = self.app_data["netlist_path"]
        optimization_settings = self.app_data["optimization_settings"]

        if not netlist_path:
            messagebox.showerror("Error", "No netlist file selected.")
            return

        optimization_type = optimization_settings["optimization_type"]

        if optimization_type == "Curve Fit":
            target_curve_filepath = optimization_settings["curve_file"]
            # Use expressions if available, otherwise use selected parameters
            x_var = (
                optimization_settings["x_parameter_expression"]
                if "x_parameter_expression" in optimization_settings
                and optimization_settings["x_parameter_expression"]
                else optimization_settings.get("x_parameter", "")
            )
            y_var = (
                optimization_settings["y_parameter_expression"]
                if "y_parameter_expression" in optimization_settings
                and optimization_settings["y_parameter_expression"]
                else optimization_settings.get("y_parameter", "")
            )
            # Get max_iterations and convert to integer, with a default value
            try:
                max_iterations = int(
                    optimization_settings.get("iterations", 100)
                )  # Default to 100
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Invalid value for Max Iterations.  Using default value of 100",
                )
                max_iterations = 100

            if not all([target_curve_filepath, x_var, y_var]):
                messagebox.showerror("Error", "Missing curve fitting parameters.")
                return

            # --- CORRECT COMPONENT EXTRACTION ---
            try:
                initial_netlist_components, _ = parse_netlist(
                    netlist_path
                )  # Parse here, get components
                variable_components = [
                    comp.name for comp in initial_netlist_components if comp.variable
                ]
            except Exception as e:
                messagebox.showerror("Error", f"Error reading netlist: {e}")
                return

            # Put all the arguments into a dictionary.
            optimization_args = {
                "target_curve_filepath": target_curve_filepath,
                "netlist_filepath": netlist_path,
                "x_var": x_var,
                "y_var": y_var,
                "variable_components": variable_components,
                "max_iterations": max_iterations,
            }

            # --- 2. Start the optimization thread ---
            self.optimization_thread = threading.Thread(
                target=self._run_optimization, args=(optimization_args,)
            )
            self.optimization_thread.start()

        else:
            messagebox.showerror("Error", "Optimization type not yet supported.")
            return

        # --- 3. Start polling the message queue ---
        self.root.after(100, self.process_queue)

    def _run_optimization(self, optimization_args: Dict[str, Any]):
        """
        This function runs in a separate thread.  It calls the *backend*
        optimization function and puts messages into the queue.
        """
        try:
            # Unpack arguments and call the *backend* optimization function.
            result = curvefit_optimize(**optimization_args)
            # Put a "COMPLETE" message into the queue, along with the results.
            self.message_queue.put((MSG_OPTIMIZATION_COMPLETE, result))
        except Exception as e:
            # Put an "ERROR" message into the queue, along with the exception.
            self.message_queue.put((MSG_OPTIMIZATION_ERROR, e))

    def process_queue(self):
        """
        Checks the message queue for messages from the backend and processes them.
        This runs periodically in the Tkinter main thread.
        """
        try:
            # Get all messages currently in the queue (non-blocking).
            while True:  # Keep getting messages until Empty is raised
                message, data = self.message_queue.get_nowait()

                if message == MSG_OPTIMIZATION_COMPLETE:
                    messagebox.showinfo(
                        "Optimization Complete", "Optimization finished!"
                    )
                    print("Optimization Result:", data)  # data is the OptimizeResult
                    # TODO: Display results in the UI (new window, plots, etc.)

                elif message == MSG_OPTIMIZATION_ERROR:
                    messagebox.showerror(
                        "Optimization Error", str(data)
                    )  # data is the Exception

                elif message == MSG_PROGRESS_UPDATE:
                    # Handle progress updates (e.g., update a progress bar)
                    print(
                        "Progress Update:", data
                    )  # Example: data could be iteration number

                # Add more message types as needed (e.g., for progress updates)

        except queue.Empty:  # No more messages in the queue
            pass  # Do nothing, just continue

        # Schedule this function to run again after 100ms
        if self.optimization_thread and self.optimization_thread.is_alive():
            self.root.after(100, self.process_queue)
