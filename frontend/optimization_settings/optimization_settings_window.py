import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional, Tuple
from .add_constraint_dialog import AddConstraintDialog
from .edit_constraint_dialog import EditConstraintDialog
from .expression_dialog import ExpressionDialog
from .constraint_table import ConstraintTable
from .max_min_settings import MaxMinSettings
from .curve_fit_settings import CurveFitSettings
from ..utils import import_constraints_from_file, export_constraints_to_file
from backend.curvefit_optimization import curvefit_optimize


class OptimizationSettingsWindow(tk.Frame):
    def __init__(self, parent: tk.Tk, controller: "AppController"):
        super().__init__(parent)
        self.controller = controller
        self.selected_parameters = self.controller.get_app_data("selected_parameters")
        self.constraints: List[Dict[str, str]] = []
        self.nodes = self.controller.get_app_data("nodes")

        # --- Main Layout Frame ---
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Optimization Type Dropdown ---
        optimization_type_label = ttk.Label(main_frame, text="Optimization Type:")
        optimization_type_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.optimization_types = ["Maximize/Minimize", "Curve Fit"]
        self.optimization_type_var = tk.StringVar(value="Maximize/Minimize")
        optimization_type_dropdown = ttk.Combobox(
            main_frame,
            textvariable=self.optimization_type_var,
            values=self.optimization_types,
            state="readonly",
        )
        optimization_type_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)
        optimization_type_dropdown.bind(
            "<<ComboboxSelected>>", self.on_optimization_type_change
        )

        # --- Settings Panels (Max/Min and Curve Fit) ---
        self.max_min_settings = MaxMinSettings(main_frame, self.selected_parameters)
        self.max_min_settings.grid(
            row=1, column=0, columnspan=3, sticky=tk.W + tk.E
        )  # Initial display

        self.curve_fit_settings = CurveFitSettings(
            main_frame, self.selected_parameters, self.nodes
        )
        self.curve_fit_settings.grid(
            row=1, column=0, columnspan=3, sticky=tk.W + tk.E
        )  # Corrected row/column
        self.curve_fit_settings.grid_remove()  # Initially hidden

        # --- Constraints Table ---
        constraints_label = ttk.Label(main_frame, text="Constraints:")
        constraints_label.grid(
            row=2, column=0, sticky=tk.W, pady=5
        )  # Added a label, and constraints are row 2

        self.constraint_table = ConstraintTable(
            main_frame,
            self.open_add_constraint_window,  # Pass the *method* as callback
            self.remove_constraint,  # Pass remove_constraint
            self.open_edit_constraint_dialog,  # Pass edit constraint
        )
        self.constraint_table.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5
        )
        # --- Add, Remove, and Edit Buttons (within the ConstraintTable) ---
        self.button_frame = ttk.Frame(main_frame)  # Create a frame for buttons.
        self.button_frame.grid(row=4, column=2, sticky=tk.E, pady=5)
        add_constraint_button = ttk.Button(
            self.button_frame,
            text="Add Constraint",
            command=self.open_add_constraint_window,  # type: ignore
        )
        add_constraint_button.pack(side=tk.LEFT, padx=2)

        remove_constraint_button = ttk.Button(
            self.button_frame, text="Remove Constraint", command=self.remove_constraint
        )
        remove_constraint_button.pack(side=tk.LEFT, padx=2)

        edit_constraint_button = ttk.Button(
            self.button_frame, text="Edit Constraint", command=self.edit_constraint
        )
        edit_constraint_button.pack(side=tk.LEFT, padx=2)
        # --- Import/Export Buttons ---
        import_export_frame = ttk.Frame(main_frame)
        import_export_frame.grid(
            row=5, column=0, columnspan=3, sticky=tk.E, pady=5
        )  # Corrected row/column

        import_button = ttk.Button(
            import_export_frame,
            text="Import Constraints",
            command=self.import_constraints,
        )
        import_button.pack(side=tk.LEFT, padx=5)

        export_button = ttk.Button(
            import_export_frame,
            text="Export Constraints",
            command=self.export_constraints,
        )
        export_button.pack(side=tk.LEFT, padx=5)

        # --- Navigation Buttons ---
        navigation_frame = ttk.Frame(self)
        navigation_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        back_button = ttk.Button(navigation_frame, text="Back", command=self.go_back)
        back_button.pack(side=tk.LEFT, padx=5)
        continue_button = ttk.Button(
            navigation_frame, text="Begin Optimization", command=self.go_forward
        )
        continue_button.pack(side=tk.RIGHT, padx=5)

    def on_optimization_type_change(self, event=None):
        selected_type = self.optimization_type_var.get()
        if selected_type == "Maximize/Minimize":
            self.curve_fit_settings.grid_remove()
            self.max_min_settings.grid()
        elif selected_type == "Curve Fit":
            self.max_min_settings.grid_remove()
            self.curve_fit_settings.grid()

    def _parse_constraints_to_bounds(
        self,
    ) -> Tuple[Dict[str, Tuple[Optional[float], Optional[float]]], List[str]]:
        """
        Parses self.constraints into a dictionary of parameter bounds suitable for optimization libraries.

        Handles simple inequalities (>, >=, <, <=) and equality (=) constraints where one side
        is a selected parameter and the other is a numerical value (potentially with SI units).

        Args:
            self: The instance of OptimizationSettingsWindow (implicitly passed). Contains
                `self.constraints` (List[Dict[str, str]]) and
                `self.selected_parameters` (List[str]).

        Returns:
            A tuple containing:
            - parameter_bounds: Dict[str, Tuple[Optional[float], Optional[float]]] where keys are
            parameter names and values are (lower_bound, upper_bound) tuples. None indicates
            no bound in that direction. For equality ('='), both lower and upper bounds are set
            to the same value if consistent with existing bounds.
            - parse_errors: List[str] containing descriptions of any issues encountered during parsing
            (e.g., invalid format, conflicting bounds, non-numeric values).
        """
        parameter_bounds: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
        parse_errors: List[str] = []
        selected_params = (
            self.selected_parameters or []
        )  # Ensure it's a list, even if None initially

        # Initialize bounds for all selected parameters to unbounded
        for param_name in selected_params:
            parameter_bounds[param_name] = (None, None)  # (lower, upper)

        # Process each constraint provided by the user
        for i, constraint in enumerate(
            self.constraints
        ):  # Use enumerate for clear error messages
            left = constraint.get("left", "").strip()
            op = constraint.get("operator", "").strip()
            right = constraint.get("right", "").strip()

            param_name = None
            value_str = None
            is_equality = False

            # 1. Identify which side is the parameter and which is the value
            if left in selected_params:
                param_name = left
                value_str = right
            elif right in selected_params:
                param_name = right
                value_str = left
                # Flip the operator logically for bounds calculation
                op_map = {">": "<", ">=": "<=", "<": ">", "<=": ">=", "=": "="}
                original_op = op
                op = op_map.get(op)  # Get the flipped operator
                if op is None:  # Check if the original operator was valid for flipping
                    parse_errors.append(
                        f"Constraint #{i + 1} ('{left} {original_op} {right}'): Invalid operator '{original_op}'."
                    )
                    continue  # Skip this constraint
            else:
                # Constraint doesn't involve a parameter selected for optimization
                parse_errors.append(
                    f"Constraint #{i + 1} ('{left} {op} {right}'): Does not involve a selected parameter ('{', '.join(selected_params)}')."
                )
                continue  # Skip this constraint

            # 2. Parse the numerical value string (including common SI units)
            try:
                value_str_lower = value_str.lower()
                multiplier = 1.0
                num_part = value_str_lower

                # Define SI prefix multipliers (order by length descending for correct parsing like 'meg' vs 'm')
                suffix_map = {
                    "t": 1e12,
                    "g": 1e9,
                    "meg": 1e6,
                    "k": 1e3,
                    "m": 1e-3,
                    "u": 1e-6,
                    "µ": 1e-6,  # Handle both 'u' and micro symbol
                    "n": 1e-9,
                    "p": 1e-12,
                    "f": 1e-15,
                }

                # Find the longest matching suffix at the end of the string
                found_suffix = None
                for suffix in sorted(suffix_map.keys(), key=len, reverse=True):
                    if value_str_lower.endswith(suffix):
                        # Check if the part before the suffix is potentially a number
                        potential_num = value_str_lower[: -len(suffix)]
                        if not potential_num:
                            continue  # Handle case like just "k", which is invalid
                        try:
                            float(potential_num)  # Verify the part is numeric
                            num_part = potential_num
                            multiplier = suffix_map[suffix]
                            found_suffix = suffix
                            break  # Use the first (longest) valid suffix found
                        except ValueError:
                            pass  # Not a number before suffix, try a shorter suffix

                # Convert the numeric part (which might be the whole string if no suffix matched)
                value = float(num_part) * multiplier

            except (ValueError, TypeError):
                # Handle cases where conversion to float fails
                parse_errors.append(
                    f"Constraint #{i + 1} ('{left} {op} {right}'): Cannot parse value '{value_str}' as a number."
                )
                continue  # Skip this constraint

            # 3. Get current bounds and determine new bounds based on the operator
            current_lower, current_upper = parameter_bounds.get(
                param_name, (None, None)
            )
            new_lower, new_upper = (
                current_lower,
                current_upper,
            )  # Start with current bounds

            # Update bounds based on operator (treating >/>= as lower, </<= as upper)
            # Note: SciPy bounds are typically inclusive [lower, upper]
            if (
                op == ">"
            ):  # lower bound (exclusive -> often treated as inclusive in practice)
                if new_lower is None or value > new_lower:
                    new_lower = value
            elif op == ">=":  # lower bound (inclusive)
                if new_lower is None or value > new_lower:
                    new_lower = value
            elif op == "<":  # upper bound (exclusive -> often treated as inclusive)
                if new_upper is None or value < new_upper:
                    new_upper = value
            elif op == "<=":  # upper bound (inclusive)
                if new_upper is None or value < new_upper:
                    new_upper = value
            elif op == "=":
                is_equality = True
                # For equality, set both lower and upper bounds to the value
                # Check for immediate conflict with existing bounds *before* applying
                if (new_lower is not None and value < new_lower) or (
                    new_upper is not None and value > new_upper
                ):
                    parse_errors.append(
                        f"Constraint #{i + 1} ('{left} {op} {right}'): Equality value {value} conflicts with existing bounds [{new_lower}, {new_upper}] for {param_name}."
                    )
                    continue  # Skip applying this conflicting equality constraint
                new_lower = value
                new_upper = value
            else:
                # This case should have been caught earlier if the operator was invalid
                parse_errors.append(
                    f"Constraint #{i + 1} ('{left} {op} {right}'): Internal error - Unhandled operator '{op}'."
                )
                continue  # Skip

            # 4. Final check: ensure lower bound is not greater than upper bound
            if (
                new_lower is not None
                and new_upper is not None
                and new_lower > new_upper
            ):
                # If the conflict wasn't caused by an equality constraint reported above:
                if not is_equality:
                    parse_errors.append(
                        f"Constraint #{i + 1} ('{left} {op} {right}'): Creates conflicting bounds for {param_name} (lower={new_lower} > upper={new_upper})."
                    )
                continue  # Skip applying the update that caused the conflict

            # 5. Update the bounds dictionary for this parameter
            parameter_bounds[param_name] = (new_lower, new_upper)

        # Return the dictionary of parsed bounds and the list of errors
        return parameter_bounds, parse_errors

    def open_add_constraint_window(self):
        dialog = AddConstraintDialog(self, self.selected_parameters)
        self.wait_window(dialog)
        if dialog.constraint:
            self.add_constraint(dialog.constraint)

    def add_constraint(self, constraint: Dict[str, str]):
        self.constraints.append(constraint)  # Store the constraint
        self.constraint_table.add_constraint(
            constraint
        )  # add the constraint to the table

    def open_edit_constraint_dialog(self, constraint: Dict[str, str], index: int):
        dialog = EditConstraintDialog(self, self.selected_parameters, constraint)
        self.wait_window(dialog)  # Wait for dialog to close
        if dialog.constraint is not None:
            # update the constraint list
            self.constraints[index] = dialog.constraint
            # Update constraint to table
            self.constraint_table.update_constraint(index, dialog.constraint)

    def remove_constraint(self):
        # get selected from treeview and index
        selected_items = self.constraint_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a constraint to remove.")
            return
        # loop in reverse to prevent index issues
        for selected in reversed(selected_items):
            index = self.constraint_table.index(selected)
            self.constraint_table.delete(selected)
            del self.constraints[index]

    def edit_constraint(self):
        """Opens the EditConstraintDialog for the selected constraint."""
        selected_items = self.constraint_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a constraint to edit.")
            return
        if len(selected_items) > 1:
            messagebox.showinfo("Info", "Please select only one constraint to edit.")
            return

        selected_item = selected_items[0]
        index = self.constraint_table.index(selected_item)
        #  CRUCIAL: We need to get the constraint data *from the Treeview*,
        #   NOT from the potentially outdated self.controller.constraints.
        values = self.constraint_table.item(selected_item, "values")
        constraint = {"left": values[0], "operator": values[1], "right": values[2]}
        self.open_edit_constraint_dialog(constraint, index)  # Call the edit callback

    def go_back(self):
        self.controller.navigate("parameter_selection")

    def go_forward(self):
        optimization_settings = {
            "optimization_type": self.optimization_type_var.get(),
            "constraints": self.constraints,
        }
        if self.optimization_type_var.get() == "Maximize/Minimize":
            optimization_settings.update(self.max_min_settings.get_settings())
        elif self.optimization_type_var.get() == "Curve Fit":
            optimization_settings.update(self.curve_fit_settings.get_settings())

        self.controller.update_app_data("optimization_settings", optimization_settings)
        # print(self.controller.get_app_data("optimization_settings"))
        curveData = self.controller.get_app_data("optimization_settings")
        # Replace with self.controller.get_app_data("optimization_settings) stuff
        # TODO Get App data to set variable components to True and the
        TARGET_VALUE = "V(2)"
        TEST_ROWS = [
            [0.00000000e00, 4.00000000e00],
            [4.00000000e-04, 4.00000000e00],
            [8.00000000e-04, 4.00000000e00],
            [1.20000000e-03, 4.00000000e00],
            [1.60000000e-03, 4.00000000e00],
            [2.00000000e-03, 4.00000000e00],
        ]
        ORIG_NETLIST_PATH = self.controller.get_app_data("netlist_path")
        TEST_NETLIST = self.controller.get_app_data("netlist_object")
        print("HELOOOOOSOSODSOD")
        print(TEST_NETLIST)
        WRITABLE_NETLIST_PATH = ORIG_NETLIST_PATH[:-4] + "Copy.txt"
        # ASK Brandon why all true and the node constraints
        for component in TEST_NETLIST.components:
            component.variable = True
        NODE_CONSTRAINTS = {"V(2)": (None, 4.1)}
        NODE_CONSTRAINTS = {}
        optim = curvefit_optimize(
            TARGET_VALUE,
            TEST_ROWS,
            TEST_NETLIST,
            WRITABLE_NETLIST_PATH,
            NODE_CONSTRAINTS,
        )
        self.controller.update_app_data("netlist_object", TEST_NETLIST)
        self.controller.update_app_data("optimization_results", optim)
        print(optim)
        print("Continue to next window (implementation needed)...")
        self.controller.navigate("optimization_summary")

    def import_constraints(self):
        """Imports constraints from a JSON file."""
        constraints = import_constraints_from_file()
        if constraints is not None:
            # Clear existing constraints
            self.constraints = []
            self.constraint_table.clear()  # Clear the Treeview

            # Add the imported constraints
            for constraint in constraints:
                self.add_constraint(constraint)
            messagebox.showinfo("Info", "Constraints imported successfully.")

    def export_constraints(self):
        """Exports constraints to a JSON file."""
        if not self.constraints:
            messagebox.showwarning("Warning", "No constraints to export.")
            return
        export_constraints_to_file(self.constraints)
