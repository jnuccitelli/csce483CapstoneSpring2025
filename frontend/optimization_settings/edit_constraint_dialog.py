import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional
from .expression_evaluator import ExpressionEvaluator


class EditConstraintDialog(tk.Toplevel):
    def __init__(self, parent, parameters: List[str], constraint: Dict[str, str]):
        super().__init__(parent)
        self.title("Edit Constraint")
        self.parameters = parameters
        self.constraint: Optional[Dict[str, str]] = (
            constraint  # Use Optional, might be None
        )
        self.evaluator = ExpressionEvaluator(parameters)

        # --- Left Expression ---
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, padx=5, pady=5)
        left_label = ttk.Label(left_frame, text="Left:")
        left_label.pack()
        self.left_var = tk.StringVar(value=constraint["left"])  # Pre-populate
        left_entry = ttk.Entry(left_frame, textvariable=self.left_var, width=15)
        left_entry.pack(side=tk.LEFT)

        # --- Operator ---
        operator_frame = ttk.Frame(self)
        operator_frame.pack(side=tk.LEFT, padx=5, pady=5)
        operator_label = ttk.Label(operator_frame, text="Operator:")
        operator_label.pack()
        self.operator_var = tk.StringVar(value=constraint["operator"])  # Pre-populate
        operators = ["=", ">=", "<="]
        for op in operators:
            op_radio = ttk.Radiobutton(
                operator_frame, text=op, variable=self.operator_var, value=op
            )
            op_radio.pack(anchor=tk.W)

        # --- Right Expression/Value ---
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.LEFT, padx=5, pady=5)
        right_label = ttk.Label(right_frame, text="Right:")
        right_label.pack()
        self.right_var = tk.StringVar(value=constraint["right"])  # Pre-populate
        right_entry = ttk.Entry(right_frame, textvariable=self.right_var, width=15)
        right_entry.pack(side=tk.LEFT)

        # --- OK and Cancel Buttons ---
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        ok_button = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def on_ok(self):
        left = self.left_var.get().strip()
        operator = self.operator_var.get()
        right = self.right_var.get().strip()

        # Validate inputs
        if not left or not operator or not right:
            messagebox.showerror("Error", "All fields are required.")
            return

        if not self.is_valid_input(left):  # Corrected call: self.is_valid_input
            return
        if not self.is_valid_input(right):  # Corrected call: self.is_valid_input
            return

        # Update the constraint dictionary
        if self.constraint is not None:
            self.constraint["left"] = left
            self.constraint["operator"] = operator
            self.constraint["right"] = right
        else:  # This case *shouldn't* happen, but it's good to be defensive
            self.constraint = {"left": left, "operator": operator, "right": right}

        self.destroy()

    def on_cancel(self):
        # Don't change the constraint
        self.destroy()

    def is_valid_input(self, input_str: str) -> bool:
        """Validates an input string as either a valid expression or a number."""
        is_valid_expr, used_vars = self.evaluator.validate_expression(input_str)
        if is_valid_expr:
            for var in used_vars:
                if var not in self.parameters:
                    messagebox.showerror(
                        "Error", f"Invalid variable '{var}' in expression."
                    )
                    return False
            return True
        try:
            float(input_str)
            return True
        except ValueError:
            messagebox.showerror("Error", f"Invalid expression or number: {input_str}")
            return False
