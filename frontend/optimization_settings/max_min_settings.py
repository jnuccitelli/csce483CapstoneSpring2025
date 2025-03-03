import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any
from .expression_dialog import ExpressionDialog


class MaxMinSettings(tk.Frame):
    def __init__(self, parent: tk.Frame, parameters: List[str]):
        super().__init__(parent)
        self.parameters = parameters
        self.parameter_expression_var = tk.StringVar(value="")

        # --- Max/Min Toggle ---
        self.max_min_frame = ttk.Frame(self)
        # self.max_min_frame.grid(row=0, column=2, sticky=tk.W, pady=5) # Moved to grid()

        self.max_min_var = tk.StringVar(value="Max")
        self.max_radio = ttk.Radiobutton(
            self.max_min_frame, text="Max", variable=self.max_min_var, value="Max"
        )
        self.max_radio.pack(side=tk.LEFT)
        self.min_radio = ttk.Radiobutton(
            self.max_min_frame, text="Min", variable=self.max_min_var, value="Min"
        )
        self.min_radio.pack(side=tk.LEFT)

        # --- Parameter Selection and Expression ---
        self.param_expr_frame = ttk.Frame(
            self
        )  # Keep param_expr_frame as attribute of MaxMinSettings
        # self.param_expr_frame.grid(row=1, column=1, sticky=tk.W, pady=5) # Moved to grid

        self.parameter_label = ttk.Label(self.param_expr_frame, text="Parameter:")
        self.parameter_label.pack(
            side=tk.LEFT, padx=5
        )  # Use pack within param_expr_frame

        self.parameter_var = tk.StringVar(value="Select Parameter")

        self.parameter_dropdown = ttk.Combobox(
            self.param_expr_frame,
            textvariable=self.parameter_var,
            values=self.parameters,
            state="readonly",
        )
        self.parameter_dropdown.pack(
            side=tk.LEFT, padx=5
        )  # Use pack within param_expr_frame
        self.parameter_dropdown.bind("<<ComboboxSelected>>", self.on_parameter_selected)

        expression_button = ttk.Button(
            self.param_expr_frame, text="Expr...", command=self.open_expression_dialog
        )
        expression_button.pack(side=tk.LEFT)  # Use pack within param_expr_frame

        # --- Iterations Input ---
        self.iterations_label = ttk.Label(self, text="Max Iterations:")
        # self.iterations_label.grid(row=2, column=0, sticky=tk.W, pady=5) # Moved to grid

        self.iterations_var = tk.StringVar(value="100")
        self.iterations_entry = ttk.Entry(self, textvariable=self.iterations_var)
        # self.iterations_entry.grid(row=2, column=1, sticky=tk.W, pady=5) # Moved to grid.

    def open_expression_dialog(self):
        dialog = ExpressionDialog(self, self.parameters)
        self.wait_window(dialog)
        if dialog.expression:
            self.parameter_expression_var.set(dialog.expression)
            self.parameter_var.set(f"Expr: {dialog.expression}")

    def on_parameter_selected(self, event=None):
        self.parameter_expression_var.set("")

    def get_settings(self) -> Dict[str, Any]:
        settings = {
            "max_min": self.max_min_var.get(),
            "iterations": self.iterations_var.get(),
        }
        if self.parameter_expression_var.get():
            settings["parameter_expression"] = self.parameter_expression_var.get()
        else:
            settings["parameter"] = self.parameter_var.get()
        return settings

    def grid(self, *args, **kwargs):
        super().grid(*args, **kwargs)  # Call original grid method
        self.max_min_frame.grid(row=0, column=2, sticky=tk.W, pady=5)
        self.param_expr_frame.grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=5
        )  # Grid relative to *self*
        self.iterations_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.iterations_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

    def grid_remove(self):
        super().grid_remove()  # Call original grid_remove method
        self.max_min_frame.grid_remove()
        self.param_expr_frame.grid_remove()  # Remove param_expr_frame
        self.iterations_label.grid_remove()
        self.iterations_entry.grid_remove()
