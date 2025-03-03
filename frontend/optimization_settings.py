import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional, Dict, Any, Tuple
import re
import math
import ast


class ExpressionEvaluator:
    """
    Handles the safe evaluation of mathematical expressions with support for
    variable substitution.
    """

    _allowed_names: Dict[str, Any] = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "log": math.log,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
    }

    def __init__(self, allowed_variables: List[str] = None) -> None:
        if allowed_variables is None:
            self.allowed_variables = []
        else:
            self.allowed_variables = allowed_variables

    def evaluate(self, expression: str, variables: Dict[str, float]) -> float:
        """
        Safely evaluates a mathematical expression, substituting variables.

        Args:
            expression: The expression string.
            variables:  A dictionary mapping variable names to their values.

        Returns:
            The result of the expression.

        Raises:
            ValueError: If the expression is invalid or contains disallowed
                names.
        """
        # Check if the expression contains only allowed characters and names
        allowed_chars_pattern = r"^[a-zA-Z0-9+\-*/().\s]+$"
        if not re.match(allowed_chars_pattern, expression):
            raise ValueError("Invalid characters in expression.")
        # Validate the expression using AST parsing for security
        try:
            parsed_expression = ast.parse(expression, mode="eval")
            for node in ast.walk(parsed_expression):
                if isinstance(node, ast.Name):
                    if (
                        node.id not in self._allowed_names
                        and node.id not in self.allowed_variables
                    ):
                        raise ValueError(f"Invalid name in expression: {node.id}")
                elif isinstance(node, ast.Call):
                    if (
                        not isinstance(node.func, ast.Name)
                        or node.func.id not in self._allowed_names
                    ):
                        raise ValueError(
                            f"Invalid function call in expression: {node.func.id if isinstance(node.func, ast.Name) else 'Unknown'}"
                        )  # type: ignore
        except SyntaxError as e:
            raise ValueError(f"Syntax error in expression: {e}") from e
        # Create safe namespace
        safe_namespace = {
            **self._allowed_names,
            **{
                var: variables[var]
                for var in variables
                if var in self.allowed_variables
            },
        }
        # Evaluate
        try:
            compiled_expression = compile(parsed_expression, "<string>", "eval")
            result = eval(compiled_expression, safe_namespace)
            return float(result)
        except (TypeError, NameError, AttributeError) as e:
            raise ValueError(f"Evaluation error: {e}") from e
        except Exception as e:
            raise ValueError(f"Unexpected error in expression evaluation: {e}") from e

    def validate_expression(self, expression: str) -> Tuple[bool, List[str]]:
        """
        Validates a mathematical expression, checking for allowed characters,
        functions, and variables.

        Args:
            expression: The expression string to validate.

        Returns:
            A tuple: (is_valid, used_variables).
            - is_valid: True if the expression is valid, False otherwise.
            - used_variables: A list of variable names found in the expression.

        Raises:
            Nothing, return type used.
        """
        # Check for allowed characters
        allowed_chars_pattern = r"^[a-zA-Z0-9+\-*/().\s=><]+$"
        if not re.match(allowed_chars_pattern, expression):
            return False, []

        # Extract potential variable names
        potential_variables = re.findall(r"[a-zA-Z][a-zA-Z0-9]*", expression)
        used_variables = []

        # Validate using AST parsing
        try:
            parsed_expression = ast.parse(expression, mode="eval")
            for node in ast.walk(parsed_expression):
                if isinstance(node, ast.Name):
                    # Check if it's a valid variable or allowed function
                    if (
                        node.id not in self._allowed_names
                        and node.id not in self.allowed_variables
                    ):
                        return False, []  # Invalid variable name
                    if node.id in potential_variables:
                        used_variables.append(node.id)
                elif isinstance(node, ast.Call):
                    # Check if it's an allowed function
                    if (
                        not isinstance(node.func, ast.Name)
                        or node.func.id not in self._allowed_names
                    ):
                        return False, []  # Invalid function call
        except SyntaxError:
            return False, []  # Invalid syntax

        return True, used_variables


class OptimizationSettingsWindow(tk.Frame):
    def __init__(self, parent: tk.Tk, controller: "AppController"):
        super().__init__(parent)
        self.controller = controller
        self.selected_parameters = self.controller.get_app_data("selected_parameters")
        self.constraints: List[dict] = []
        self.evaluator = ExpressionEvaluator(self.selected_parameters)

        # --- Main Layout Frame ---
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Optimization Type Dropdown ---
        optimization_type_label = ttk.Label(main_frame, text="Optimization Type:")
        optimization_type_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.optimization_types = [
            "Maximize/Minimize",
            "Curve Fit",
        ]  # Removed expression option
        self.optimization_type_var = tk.StringVar(value="Maximize/Minimize")
        self.optimization_type_dropdown = ttk.Combobox(
            main_frame,
            textvariable=self.optimization_type_var,
            values=self.optimization_types,
            state="readonly",
        )
        self.optimization_type_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.optimization_type_dropdown.bind(
            "<<ComboboxSelected>>", self.on_optimization_type_change
        )

        # --- Max/Min Toggle ---
        self.max_min_frame = ttk.Frame(main_frame)
        self.max_min_frame.grid(row=0, column=2, sticky=tk.W, pady=5)

        self.max_min_var = tk.StringVar(value="Max")
        self.max_radio = ttk.Radiobutton(
            self.max_min_frame, text="Max", variable=self.max_min_var, value="Max"
        )
        self.max_radio.pack(side=tk.LEFT)
        self.min_radio = ttk.Radiobutton(
            self.max_min_frame, text="Min", variable=self.max_min_var, value="Min"
        )
        self.min_radio.pack(side=tk.LEFT)

        # --- Parameter Selection and Expression (for Maximize/Minimize) ---
        param_expr_frame = ttk.Frame(main_frame)  # Frame to hold dropdown and button
        self.param_expr_frame = param_expr_frame  # Make it an attribute
        self.parameter_label = ttk.Label(main_frame, text="Parameter:")
        self.parameter_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        self.parameter_var = tk.StringVar(value="Select Parameter")
        # Keep track of whether an expression is being used
        self.parameter_expression_var = tk.StringVar(value="")

        self.parameter_dropdown = ttk.Combobox(
            param_expr_frame,  # Parent is now the frame
            textvariable=self.parameter_var,
            values=self.selected_parameters,
            state="readonly",
        )
        self.parameter_dropdown.pack(side=tk.LEFT, padx=5)
        self.parameter_dropdown.bind("<<ComboboxSelected>>", self.on_parameter_selected)

        expression_button = ttk.Button(
            param_expr_frame, text="Expr...", command=self.open_expression_dialog
        )
        expression_button.pack(side=tk.LEFT)

        param_expr_frame.grid(row=1, column=1, sticky=tk.W, pady=5)  # Place the frame

        # --- Iterations Input (for Max/Min) ---
        iterations_label = ttk.Label(main_frame, text="Max Iterations:")
        iterations_label.grid(row=2, column=0, sticky=tk.W, pady=5)

        self.iterations_var = tk.StringVar(value="100")
        self.iterations_entry = ttk.Entry(main_frame, textvariable=self.iterations_var)
        self.iterations_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

        # --- Curve Fit File Picker ---
        self.curve_fit_frame = ttk.Frame(main_frame)

        curve_fit_button = ttk.Button(
            self.curve_fit_frame,
            text="Select Curve File",
            command=self.select_curve_file,
        )
        curve_fit_button.pack()

        self.curve_file_path_var = tk.StringVar(value="")
        curve_file_label = ttk.Label(
            self.curve_fit_frame, textvariable=self.curve_file_path_var
        )
        curve_file_label.pack()

        # --- X and Y Parameter Dropdowns and Expressions (for Curve Fit) ---
        x_param_label = ttk.Label(self.curve_fit_frame, text="X Parameter:")
        x_param_label.pack(side=tk.LEFT, padx=5)
        self.x_parameter_var = tk.StringVar()
        self.x_parameter_expression_var = tk.StringVar()  # For X expression
        x_param_frame = ttk.Frame(self.curve_fit_frame)  # frame
        self.x_parameter_dropdown = ttk.Combobox(
            x_param_frame,
            textvariable=self.x_parameter_var,
            values=self.selected_parameters,
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

        y_param_label = ttk.Label(self.curve_fit_frame, text="Y Parameter:")
        y_param_label.pack(side=tk.LEFT, padx=5)
        self.y_parameter_var = tk.StringVar()
        self.y_parameter_expression_var = tk.StringVar()  # For Y expression
        y_param_frame = ttk.Frame(self.curve_fit_frame)
        self.y_parameter_dropdown = ttk.Combobox(
            y_param_frame,
            textvariable=self.y_parameter_var,
            values=self.selected_parameters,
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

        # --- Constraints Table ---
        constraints_label = ttk.Label(main_frame, text="Constraints:")
        constraints_label.grid(row=3, column=0, sticky=tk.W, pady=5)

        self.constraints_table = ttk.Treeview(
            main_frame, columns=("Left", "Operator", "Right"), show="headings"
        )
        self.constraints_table.heading("Left", text="Left")
        self.constraints_table.heading("Operator", text="Operator")
        self.constraints_table.heading("Right", text="Right")
        self.constraints_table.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )
        self.constraints_table.column("Left", width=100)
        self.constraints_table.column("Operator", width=50)
        self.constraints_table.column("Right", width=100)

        # --- Add Constraint Button ---
        add_constraint_button = ttk.Button(
            main_frame, text="Add Constraint", command=self.open_add_constraint_window
        )
        add_constraint_button.grid(row=3, column=2, sticky=tk.E, pady=5)

        # --- Remove Constraint Button ---
        remove_constraint_button = ttk.Button(
            main_frame, text="Remove Constraint", command=self.remove_constraint
        )
        remove_constraint_button.grid(row=4, column=2, sticky=tk.NE, pady=5)

        # --- Navigation Buttons ---
        navigation_frame = ttk.Frame(self)
        navigation_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        back_button = ttk.Button(navigation_frame, text="Back", command=self.go_back)
        back_button.pack(side=tk.LEFT, padx=5)

        continue_button = ttk.Button(
            navigation_frame, text="Continue", command=self.go_forward
        )
        continue_button.pack(side=tk.RIGHT, padx=5)

    def on_optimization_type_change(self, event=None):
        selected_type = self.optimization_type_var.get()
        if selected_type == "Maximize/Minimize":
            self.curve_fit_frame.grid_remove()
            self.max_min_frame.grid()
            # self.parameter_dropdown.grid()
            self.param_expr_frame.grid()  # show expression frame
            self.iterations_entry.grid()
            # self.expression_frame.grid_remove()
            self.parameter_label.grid()  # Need to remake label
        elif selected_type == "Curve Fit":
            self.max_min_frame.grid_remove()
            # self.parameter_dropdown.grid_remove()
            self.param_expr_frame.grid_remove()
            self.iterations_entry.grid_remove()
            self.curve_fit_frame.grid(
                row=1, column=0, columnspan=3, sticky=tk.W, pady=5
            )
            # self.expression_frame.grid_remove()
            self.parameter_label.grid_remove()

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

    def open_add_constraint_window(self):
        dialog = AddConstraintDialog(self, self.selected_parameters)
        self.wait_window(dialog)
        if dialog.constraint:
            self.add_constraint(dialog.constraint)

    def add_constraint(self, constraint: dict):
        self.constraints.append(constraint)
        self.constraints_table.insert(
            "",
            tk.END,
            values=(
                constraint["left"],
                constraint["operator"],
                constraint["right"],
            ),
        )

    def remove_constraint(self):
        selected_items = self.constraints_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a constraint to remove.")
            return
        for selected_item in reversed(selected_items):
            index = self.constraints_table.index(selected_item)
            self.constraints_table.delete(selected_item)
            del self.constraints[index]

    def go_back(self):
        self.controller.navigate("parameter_selection")

    def go_forward(self):
        # Collect data based on optimization type
        optimization_type = self.optimization_type_var.get()
        optimization_settings: Dict[str, Any] = {
            "optimization_type": optimization_type,
            "constraints": self.constraints,
        }
        # Maximize/Minimize
        if optimization_type == "Maximize/Minimize":
            optimization_settings["max_min"] = self.max_min_var.get()
            # Check if an expression is used
            if self.parameter_expression_var.get():
                optimization_settings["parameter_expression"] = (
                    self.parameter_expression_var.get()
                )
            else:
                optimization_settings["parameter"] = self.parameter_var.get()

            optimization_settings["iterations"] = self.iterations_var.get()
        # Curve Fit
        elif optimization_type == "Curve Fit":
            optimization_settings["curve_file"] = self.curve_file_path_var.get()
            # Check if expressions are used for X and Y
            if self.x_parameter_expression_var.get():
                optimization_settings["x_parameter_expression"] = (
                    self.x_parameter_expression_var.get()
                )
            else:
                optimization_settings["x_parameter"] = self.x_parameter_var.get()

            if self.y_parameter_expression_var.get():
                optimization_settings["y_parameter_expression"] = (
                    self.y_parameter_expression_var.get()
                )
            else:
                optimization_settings["y_parameter"] = self.y_parameter_var.get()

        self.controller.update_app_data("optimization_settings", optimization_settings)
        print("Continue to next window (implementation needed)...")

    def open_expression_dialog(self, is_x=False):
        # is_x is used for curve fitting for x and y coordinate expressions
        dialog = ExpressionDialog(self, self.selected_parameters)
        self.wait_window(dialog)
        if dialog.expression:
            expression = dialog.expression
            # Maximize/Minimize
            if hasattr(self, "parameter_expression_var"):
                self.parameter_expression_var.set(expression)
                self.parameter_var.set(
                    f"Expr: {expression}"
                )  # Show expression in dropdown
            # Curve fitting
            if is_x:
                self.x_parameter_expression_var.set(expression)
                self.x_parameter_var.set(f"Expr: {expression}")
            else:
                self.y_parameter_expression_var.set(expression)
                self.y_parameter_var.set(f"Expr: {expression}")

    def on_parameter_selected(self, event=None):
        # Clear the expression if a regular parameter is selected
        self.parameter_expression_var.set("")

    def on_x_parameter_selected(self, event=None):
        self.x_parameter_expression_var.set("")

    def on_y_parameter_selected(self, event=None):
        self.y_parameter_expression_var.set("")


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
