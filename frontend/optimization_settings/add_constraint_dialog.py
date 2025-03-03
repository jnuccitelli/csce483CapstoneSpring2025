import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional
from .expression_evaluator import ExpressionEvaluator


class AddConstraintDialog(tk.Toplevel):
    def __init__(self, parent, parameters: List[str]):
        super().__init__(parent)
        self.title("Add Constraint")
        self.parameters = parameters
        self.constraint: Optional[Dict[str, str]] = None  # Use Optional for clarity
        self.evaluator = ExpressionEvaluator(parameters)

        # --- Left Expression ---
        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, padx=5, pady=5)
        left_label = ttk.Label(left_frame, text="Left:")
        left_label.pack()
        self.left_var = tk.StringVar()
        left_entry = ttk.Entry(left_frame, textvariable=self.left_var, width=15)
        left_entry.pack(side=tk.LEFT)

        # --- Operator ---
        operator_frame = ttk.Frame(self)
        operator_frame.pack(side=tk.LEFT, padx=5, pady=5)
        operator_label = ttk.Label(operator_frame, text="Operator:")
        operator_label.pack()
        self.operator_var = tk.StringVar(value="=")  # Default to equals
        operators = ["=", ">=", "<="]
        for op in operators:
            op_radio = ttk.Radiobutton(
                operator_frame, text=op, variable=self.operator_var, value=op
            )
            op_radio.pack(anchor=tk.W)  # Left-align radio buttons

        # --- Right Expression/Value ---
        right_frame = ttk.Frame(self)
        right_frame.pack(side=tk.LEFT, padx=5, pady=5)
        right_label = ttk.Label(right_frame, text="Right:")
        right_label.pack()
        self.right_var = tk.StringVar()
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

        # Validate expressions
        if not self.is_valid_input(left):
            return
        if not self.is_valid_input(right):
            return
        self.constraint = {"left": left, "operator": operator, "right": right}
        self.destroy()

    def on_cancel(self):
        self.constraint = None
        self.destroy()

    def is_valid_input(self, input_str: str) -> bool:
        """Validates an input string as either a valid expression or a number."""
        # First, try to validate as an expression
        is_valid_expr, used_vars = self.evaluator.validate_expression(input_str)
        if is_valid_expr:
            # Check if all used variables are in the allowed parameters
            for var in used_vars:
                if var not in self.parameters:
                    messagebox.showerror(
                        "Error",
                        f"Invalid variable '{var}' in expression.  Must be one of {self.parameters}",
                    )
                    return False
            return True

        # If not a valid expression, check if it's a valid number
        try:
            float(input_str)  # Check if it can be a float
            return True
        except ValueError:
            messagebox.showerror("Error", f"Invalid expression or number: {input_str}")
            return False
