import tkinter as tk
from tkinter import ttk, filedialog
from typing import List, Dict, Any
from .expression_dialog import ExpressionDialog


class CurveFitSettings(tk.Frame):
    def __init__(self, parent: tk.Frame, parameters: List[str], nodes: List[str]):
        super().__init__(parent)
        self.parameters = parameters
        self.nodes = nodes
        self.x_parameter_expression_var = tk.StringVar()
        self.y_parameter_expression_var = tk.StringVar()

        # --- Curve Fit File Picker ---
        curve_fit_button = ttk.Button(
            self, text="Select Curve File", command=self.select_curve_file
        )
        curve_fit_button.pack()

        self.curve_file_path_var = tk.StringVar(value="")
        curve_file_label = ttk.Label(self, textvariable=self.curve_file_path_var)
        curve_file_label.pack()

        # --- X and Y Parameter Dropdowns and Expressions ---
        x_param_label = ttk.Label(self, text="X Parameter:")
        x_param_label.pack(side=tk.LEFT, padx=5)
        self.x_parameter_var = tk.StringVar()
        x_param_frame = ttk.Frame(self)
        self.x_parameter_dropdown = ttk.Combobox(
            x_param_frame,
            textvariable=self.x_parameter_var,
            values=["time"],  # Corrected to "time"
            state="readonly",
        )
        self.x_parameter_dropdown.pack(side=tk.LEFT, padx=5)
        self.x_parameter_dropdown.bind(
            "<<ComboboxSelected>>", self.on_x_parameter_selected
        )
        x_expression_button = ttk.Button(
            x_param_frame,
            text="Expr...",
            command=lambda: self.open_expression_dialog(is_x=True),
        )
        x_expression_button.pack(side=tk.LEFT)
        x_param_frame.pack(side=tk.LEFT, padx=5)

        y_param_label = ttk.Label(self, text="Y Parameter:")
        y_param_label.pack(side=tk.LEFT, padx=5)
        self.y_parameter_var = tk.StringVar()

        y_param_frame = ttk.Frame(self)
        self.y_parameter_dropdown = ttk.Combobox(
            y_param_frame,
            textvariable=self.y_parameter_var,
            values=[f"V({node})" for node in self.nodes],  # Use node voltages
            state="readonly",
        )
        self.y_parameter_dropdown.pack(side=tk.LEFT, padx=5)
        self.y_parameter_dropdown.bind(
            "<<ComboboxSelected>>", self.on_y_parameter_selected
        )

        y_expression_button = ttk.Button(
            y_param_frame,
            text="Expr...",
            command=lambda: self.open_expression_dialog(is_x=False),
        )
        y_expression_button.pack(side=tk.LEFT)
        y_param_frame.pack(side=tk.LEFT, padx=5)

        # --- Horizontal Line Value ---
        hline_frame = ttk.Frame(self)
        hline_frame.pack(pady=5)  # Added padding
        hline_label = ttk.Label(hline_frame, text="Horizontal Line Value:")
        hline_label.pack(side=tk.LEFT, padx=5)
        self.hline_value_var = tk.StringVar(value="")
        hline_entry = ttk.Entry(hline_frame, textvariable=self.hline_value_var)
        hline_entry.pack(side=tk.LEFT, padx=5)

        # --- Maximum Iterations ---
        iterations_frame = ttk.Frame(self)
        iterations_frame.pack(pady=5)
        iterations_label = ttk.Label(iterations_frame, text="Max Iterations:")
        iterations_label.pack(side=tk.LEFT, padx=5)
        self.iterations_var = tk.StringVar(value="100")  # Default value
        iterations_entry = ttk.Entry(iterations_frame, textvariable=self.iterations_var)
        iterations_entry.pack(side=tk.LEFT, padx=5)

    def select_curve_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a Curve File",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("Text Files", "*.txt"),
                ("DAT Files", "*.dat"),
                ("All Files", "*.*"),
            ],
        )
        if file_path:
            self.curve_file_path_var.set(file_path)

    def open_expression_dialog(self, is_x=False):
        dialog = ExpressionDialog(self, self.parameters)
        self.wait_window(dialog)
        if dialog.expression:
            if is_x:
                self.x_parameter_expression_var.set(dialog.expression)
                self.x_parameter_var.set(f"Expr: {dialog.expression}")
            else:
                self.y_parameter_expression_var.set(dialog.expression)
                self.y_parameter_var.set(f"Expr: {dialog.expression}")

    def on_x_parameter_selected(self, event=None):
        self.x_parameter_expression_var.set("")

    def on_y_parameter_selected(self, event=None):
        self.y_parameter_expression_var.set("")

    def get_settings(self) -> Dict[str, Any]:
        settings = {
            "curve_file": self.curve_file_path_var.get(),
            "hline_value": self.hline_value_var.get(),
            "iterations": self.iterations_var.get(),
        }
        if self.x_parameter_expression_var.get():
            settings["x_parameter_expression"] = self.x_parameter_expression_var.get()
        else:
            settings["x_parameter"] = self.x_parameter_var.get()

        if self.y_parameter_expression_var.get():
            settings["y_parameter_expression"] = self.y_parameter_expression_var.get()
        else:
            settings["y_parameter"] = self.y_parameter_var.get()
        return settings
