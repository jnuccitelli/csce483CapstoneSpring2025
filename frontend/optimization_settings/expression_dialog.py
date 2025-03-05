import tkinter as tk
from tkinter import ttk, messagebox
from typing import List
from .expression_evaluator import ExpressionEvaluator  # Import the evaluator


class ExpressionDialog(tk.Toplevel):
    def __init__(self, parent, parameters: List[str]):
        super().__init__(parent)
        self.title("Enter Expression")
        self.parameters = parameters
        self.expression = None
        self.evaluator = ExpressionEvaluator(parameters)

        # --- Expression Entry ---
        expression_label = ttk.Label(self, text="Expression:")
        expression_label.pack(pady=5)

        self.expression_var = tk.StringVar()
        expression_entry = ttk.Entry(
            self, textvariable=self.expression_var, width=40
        )  # Increased width
        expression_entry.pack(padx=5, pady=5)

        # --- OK and Cancel Buttons ---
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ok_button = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def on_ok(self):
        expression = self.expression_var.get().strip()
        if not expression:
            messagebox.showerror("Error", "Please enter an expression.")
            return

        # Validate expression
        is_valid, used_vars = self.evaluator.validate_expression(expression)
        if not is_valid:
            messagebox.showerror("Error", f"Invalid expression {expression}")
            return
        # Check if all used variables are in the allowed parameters
        for var in used_vars:
            if var not in self.parameters:
                messagebox.showerror(
                    "Error",
                    f"Invalid variable '{var}' in expression. Must be one of {self.parameters}",
                )
                return
        self.expression = expression
        self.destroy()

    def on_cancel(self):
        self.expression = None
        self.destroy()
