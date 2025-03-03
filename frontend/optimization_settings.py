import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional, Dict, Any
import re
import math


class OptimizationSettingsWindow(tk.Frame):
    def __init__(self, parent: tk.Tk, controller: "AppController"):
        super().__init__(parent)
        self.controller = controller
        self.selected_parameters = self.controller.get_app_data("selected_parameters")
        self.constraints: List[dict] = []

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
            main_frame, columns=("Parameter", "Type", "Value"), show="headings"
        )
        self.constraints_table.heading("Parameter", text="Parameter")
        self.constraints_table.heading("Type", text="Type")
        self.constraints_table.heading("Value", text="Value")
        self.constraints_table.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )
        self.constraints_table.column("Parameter", width=100)
        self.constraints_table.column("Type", width=50)
        self.constraints_table.column("Value", width=100)

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
        if "type" not in constraint:
            self.constraints_table.insert(
                "", tk.END, values=("Custom", "", constraint["expression"])
            )
        else:
            self.constraints_table.insert(
                "",
                tk.END,
                values=(
                    constraint["parameter"],
                    constraint["type"],
                    constraint["value"],
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
        self.constraint = None
        self.is_custom = tk.BooleanVar(value=False)

        # --- Constraint Type Frame (Radio Buttons) ---
        constraint_type_frame = ttk.Frame(self)
        constraint_type_frame.pack(pady=5)

        standard_radio = ttk.Radiobutton(
            constraint_type_frame,
            text="Standard Constraint",
            variable=self.is_custom,
            value=False,
            command=self.update_ui,
        )
        standard_radio.pack(side=tk.LEFT, padx=5)
        custom_radio = ttk.Radiobutton(
            constraint_type_frame,
            text="Custom Constraint",
            variable=self.is_custom,
            value=True,
            command=self.update_ui,
        )
        custom_radio.pack(side=tk.LEFT, padx=5)

        # --- Standard Constraint Widgets ---
        self.standard_frame = ttk.Frame(self)
        self.standard_frame.pack(fill=tk.BOTH, expand=True)

        param_label = ttk.Label(self.standard_frame, text="Variable Limit:")
        param_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.parameter_var = tk.StringVar(value="Select Parameter")
        self.parameter_dropdown = ttk.Combobox(
            self.standard_frame,
            textvariable=self.parameter_var,
            values=self.parameters,
            state="readonly",
        )
        self.parameter_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        self.constraint_type_var = tk.StringVar(value="=")
        self.value_var = tk.StringVar()

        equal_radio = ttk.Radiobutton(
            self.standard_frame,
            text="Equal",
            variable=self.constraint_type_var,
            value="=",
        )
        equal_radio.grid(row=0, column=2, sticky=tk.W, padx=5)
        lower_radio = ttk.Radiobutton(
            self.standard_frame,
            text="Lower Bound",
            variable=self.constraint_type_var,
            value=">=",
        )
        lower_radio.grid(row=0, column=3, sticky=tk.W, padx=5)
        upper_radio = ttk.Radiobutton(
            self.standard_frame,
            text="Upper Bound",
            variable=self.constraint_type_var,
            value="<=",
        )
        upper_radio.grid(row=0, column=4, sticky=tk.W, padx=5)

        value_entry = ttk.Entry(self.standard_frame, textvariable=self.value_var)
        value_entry.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)

        # --- Custom Constraint Widgets ---
        self.custom_frame = ttk.Frame(self)
        # self.custom_frame.pack(fill=tk.BOTH, expand=True)  # Initially hidden

        expression_label = ttk.Label(self.custom_frame, text="Expression:")
        expression_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.expression_var = tk.StringVar()
        expression_entry = ttk.Entry(
            self.custom_frame, textvariable=self.expression_var, width=40
        )
        expression_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # --- OK and Cancel Buttons ---
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ok_button = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)

        self.update_ui()  # Initial UI state

    def update_ui(self):
        if self.is_custom.get():
            self.standard_frame.pack_forget()
            self.custom_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.custom_frame.pack_forget()
            self.standard_frame.pack(fill=tk.BOTH, expand=True)

    def on_ok(self):
        if self.is_custom.get():
            expression = self.expression_var.get().strip()
            if not expression:
                messagebox.showerror("Error", "Please enter an expression.")
                return
            if not self.validate_expression(expression):
                return
            self.constraint = {"expression": expression}
        else:
            parameter = self.parameter_var.get()
            constraint_type = self.constraint_type_var.get()
            value = self.value_var.get()

            if parameter == "Select Parameter" or not value:
                messagebox.showerror(
                    "Error", "Please select a parameter and enter a value."
                )
                return

            try:
                float(value)
            except ValueError:
                messagebox.showerror("Error", "Invalid value. Please enter a number.")
                return

            self.constraint = {
                "parameter": parameter,
                "type": constraint_type,
                "value": value,
            }

        self.destroy()

    def on_cancel(self):
        self.constraint = None
        self.destroy()

    def validate_expression(self, expression: str) -> bool:
        """Validates the user-entered expression."""
        allowed_chars_pattern = r"^[a-zA-Z0-9+\-*/().\s=><]+$"
        if not re.match(allowed_chars_pattern, expression):
            messagebox.showerror("Error", "Invalid characters in expression.")
            return False

        potential_components = re.findall(r"[a-zA-Z][a-zA-Z0-9]*", expression)
        for comp in potential_components:
            if comp not in self.parameters and comp not in [
                "pi",
                "e",
                "sin",
                "cos",
                "tan",
                "ln",
            ]:
                messagebox.showerror("Error", f"Invalid component name: {comp}")
                return False

        safe_namespace = {
            "__builtins__": {},
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "ln": math.log,
            "pi": math.pi,
            "e": math.e,
        }
        for param in self.parameters:
            safe_namespace[param] = 1.0

        try:
            eval(expression, safe_namespace)
        except SyntaxError:
            messagebox.showerror("Error", "Invalid expression syntax.")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Invalid expression: {e}")
            return False

        return True


class ExpressionDialog(tk.Toplevel):
    def __init__(self, parent, parameters: List[str]):
        super().__init__(parent)
        self.title("Enter Expression")
        self.parameters = parameters
        self.expression: Optional[str] = None

        # --- Expression Input ---
        expression_label = ttk.Label(self, text="Expression:")
        expression_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.expression_var = tk.StringVar()
        expression_entry = ttk.Entry(self, textvariable=self.expression_var, width=40)
        expression_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # --- Available Parameters (for reference) ---
        params_label = ttk.Label(
            self, text="Available Parameters: " + ", ".join(parameters)
        )
        params_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # --- OK and Cancel Buttons ---
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ok_button = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def on_ok(self):
        expression = self.expression_var.get().strip()
        if not expression:
            messagebox.showerror("Error", "Please enter an expression.")
            return

        if not self.validate_expression(expression):
            return

        self.expression = expression
        self.destroy()

    def on_cancel(self):
        self.expression = None
        self.destroy()

    def validate_expression(self, expression: str) -> bool:
        """Validates the user-entered expression (same as before)."""
        allowed_chars_pattern = r"^[a-zA-Z0-9+\-*/().\s=><]+$"
        if not re.match(allowed_chars_pattern, expression):
            messagebox.showerror("Error", "Invalid characters in expression.")
            return False

        potential_components = re.findall(r"[a-zA-Z][a-zA-Z0-9]*", expression)
        for comp in potential_components:
            if comp not in self.parameters and comp not in [
                "pi",
                "e",
                "sin",
                "cos",
                "tan",
                "ln",
            ]:
                messagebox.showerror("Error", f"Invalid component name: {comp}")
                return False

        safe_namespace = {
            "__builtins__": {},
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "ln": math.log,
            "pi": math.pi,
            "e": math.e,
        }
        for param in self.parameters:
            safe_namespace[param] = 1.0

        try:
            eval(expression, safe_namespace)
        except SyntaxError:
            messagebox.showerror("Error", "Invalid expression syntax.")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Invalid expression: {e}")
            return False

        return True


def evaluate_expression(expression: str, component_values: Dict[str, float]) -> float:
    """Evaluates a custom constraint expression (same as before)."""
    safe_namespace = {
        "__builtins__": {},
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "ln": math.log,
        "pi": math.pi,
        "e": math.e,
    }
    safe_namespace.update(component_values)
    try:
        result = eval(expression, safe_namespace)
        return result
    except (NameError, SyntaxError, ZeroDivisionError, TypeError) as e:
        raise ValueError(f"Error evaluating expression: {e}")
