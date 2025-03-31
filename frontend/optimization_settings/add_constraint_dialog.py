import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional
from .expression_evaluator import ExpressionEvaluator


class AddConstraintDialog(tk.Toplevel):
    def __init__(self, parent, all_allowed_vars: List[str]):
        super().__init__(parent)
        self.title("Add Constraint")
        self.all_allowed_vars = all_allowed_vars
        self.constraint: Optional[Dict[str, str]] = None
        # Pass the combined list to the evaluator
        self.evaluator = ExpressionEvaluator(self.all_allowed_vars)

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

        if not left or not operator or not right:
            messagebox.showerror("Error", "All fields are required.")
            return

        # --- NEW: Validate Left Side ---
        # Check if 'left' is exactly one of the known parameters or node expressions
        is_valid_left, left_vars = self.evaluator.validate_expression(left)
        # We need a stricter check: is it *just* a name, and is that name allowed?
        # Simple check: is the raw string in our allowed list?
        if left not in self.all_allowed_vars:
            messagebox.showerror(
                "Validation Error",
                f"Invalid left-hand side: '{left}'. Must be a single selected parameter or node expression (e.g., V(node)).",
            )
            return
        # --- END NEW ---

        # --- Existing validation for Right Side (allow expressions or numbers) ---
        if not self.is_valid_input(
            right
        ):  # is_valid_input should allow numbers OR valid expressions
            return
        # --- END Existing ---

        # If all validation passes:
        # In AddConstraintDialog.on_ok:
        self.constraint = {
            "left": left,
            "operator": operator,
            "right": right,
        }  # Type added later in OptimizationSettingsWindow
        self.destroy()

        # In EditConstraintDialog.on_ok:
        if self.constraint is not None:
            self.constraint["left"] = left
            self.constraint["operator"] = operator
            self.constraint["right"] = right
            # Type will be updated in OptimizationSettingsWindow after dialog closes
        else:
            # Fallback, though shouldn't happen in edit mode
            self.constraint = {"left": left, "operator": operator, "right": right}
        self.destroy()

    def on_cancel(self):
        self.constraint = None
        self.destroy()

    def is_valid_input(self, input_str: str) -> bool:
        """Validates right-hand side as either a valid expression or a number."""
        # Try to validate as an expression using ALL allowed vars
        is_valid_expr, used_vars = self.evaluator.validate_expression(
            input_str
        )  # Evaluator uses self.all_allowed_vars

        if is_valid_expr:
            # Check if all variables used in the expression are allowed
            # (This check might be redundant if validate_expression already does it, depends on evaluator impl.)
            for var in used_vars:
                # Note: evaluator.allowed_variables should be self.all_allowed_vars now
                if var not in self.evaluator.allowed_variables:
                    messagebox.showerror(
                        "Error",
                        f"Invalid variable '{var}' in expression '{input_str}'. Allowed: {self.evaluator.allowed_variables}",
                    )
                    return False
            return True  # It's a valid expression using allowed variables/functions

        # If not a valid expression, check if it's a valid number (allow SI units maybe?)
        try:
            # TODO: Enhance to handle SI units like '1k', '0.1u' if needed for right side
            # Basic float check for now:
            float(input_str)
            return True  # It's a valid number
        except ValueError:
            messagebox.showerror(
                "Error", f"Invalid expression or number on right-hand side: {input_str}"
            )
            return False
