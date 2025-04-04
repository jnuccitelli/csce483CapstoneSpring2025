import tkinter as tk
import shutil
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional
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
        self.node_voltage_expressions = [
            f"V({node})" for node in self.nodes if node != "0"
        ]  # Exclude ground node '0' typically

        self.all_allowed_validation_vars = (
            self.selected_parameters or []
        ) + self.node_voltage_expressions
        print(
            f"Allowed Vars for Validation: {self.all_allowed_validation_vars}"
        )  # For debugging
        self.function_button_pressed = False
        self.y_param_dropdown_selected = False

        # --- Main Layout Frame ---
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Optimization Type Dropdown ---
        optimization_type_frame = ttk.Frame(main_frame)
        optimization_type_frame.pack(side=tk.TOP, fill=tk.X)
        optimization_type_label = ttk.Label(
            optimization_type_frame, text="Optimization Type:"
        )
        optimization_type_label.pack(side=tk.LEFT, anchor=tk.W, pady=5)

        self.optimization_types = ["Maximize/Minimize", "Curve Fit"]
        self.optimization_type_var = tk.StringVar(value="Curve Fit")
        optimization_type_dropdown = ttk.Combobox(
            optimization_type_frame,
            textvariable=self.optimization_type_var,
            values=self.optimization_types,
            state="readonly",
        )
        optimization_type_dropdown.pack(side=tk.LEFT, anchor=tk.W, pady=5)
        optimization_type_dropdown.bind(
            "<<ComboboxSelected>>", self.on_optimization_type_change
        )

        # --- Settings Panels (Max/Min and Curve Fit) ---
        setting_panel_frame = ttk.Frame(main_frame)
        # Pack this frame where the settings should appear
        setting_panel_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        # Instantiate CurveFitSettings, attaching it to the setting_panel_frame
        # Make sure to include the inputs_completed_callback from the main branch version
        self.curve_fit_settings = CurveFitSettings(
            setting_panel_frame,
            self.selected_parameters,
            self.nodes,
            controller,
            inputs_completed_callback=self.handle_curve_fit_conditions,  # Keep this callback
        )
        # Pack the CurveFitSettings panel so it's visible
        self.curve_fit_settings.pack(fill=tk.X)
        self.max_min_settings = MaxMinSettings(
            setting_panel_frame, self.selected_parameters
        )
        self.max_min_settings.pack(fill=tk.X)
        self.max_min_settings.pack_forget()  # Initially hidden

        # --- Constraints Table ---
        constraints_frame = ttk.Frame(main_frame)
        constraints_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        constraints_label = ttk.Label(constraints_frame, text="Constraints:")
        constraints_label.pack(
            side=tk.TOP, anchor=tk.W, pady=5
        )  # Added a label, and constraints are row 2

        self.constraint_table = ConstraintTable(
            constraints_frame,
            self.open_add_constraint_window,  # Pass the *method* as callback
            self.remove_constraint,  # Pass remove_constraint
            self.open_edit_constraint_dialog,  # Pass edit constraint
        )
        self.constraint_table.pack(fill=tk.BOTH, expand=True)

        # --- Add, Remove, and Edit Buttons (within the ConstraintTable) ---
        self.button_frame = ttk.Frame(constraints_frame)  # Create a frame for buttons.
        self.button_frame.pack(side=tk.TOP, pady=5)
        add_constraint_button = ttk.Button(
            self.button_frame,
            text="Add Constraint",
            command=self.open_add_constraint_window,  # type: ignore
        )
        add_constraint_button.pack(side=tk.LEFT, padx=5)

        remove_constraint_button = ttk.Button(
            self.button_frame, text="Remove Constraint", command=self.remove_constraint
        )
        remove_constraint_button.pack(side=tk.LEFT, padx=5)

        edit_constraint_button = ttk.Button(
            self.button_frame, text="Edit Constraint", command=self.edit_constraint
        )
        edit_constraint_button.pack(side=tk.LEFT, padx=5)


        # --- Import/Export Buttons ---
        import_export_frame = ttk.Frame(constraints_frame)

        import_export_frame.pack(side=tk.TOP, pady=2) # Corrected row/column

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
        navigation_frame.pack(side=tk.BOTTOM, fill=tk.X)

        back_button = ttk.Button(navigation_frame, text="Back", command=self.go_back)
        back_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.continue_button = ttk.Button(
            navigation_frame,
            text="Begin Optimization",
            command=self.go_forward,
            state=tk.DISABLED,
        )
        self.continue_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def handle_curve_fit_conditions(self, condition_type, state):
        """Update flags based on inputs from CurveFitSettings."""
        if condition_type == "function_button_pressed":
            self.function_button_pressed = state
        elif condition_type == "y_param_dropdown_selected":
            self.y_param_dropdown_selected = state

        # Check if all conditions are met
        self.update_continue_button_state()

    def update_continue_button_state(self):
        """Enable the 'Begin Optimization' button if all conditions are met."""
        if self.function_button_pressed and self.y_param_dropdown_selected:
            self.continue_button.config(state=tk.NORMAL)
        else:
            self.continue_button.config(state=tk.DISABLED)

    def on_optimization_type_change(self, event=None):
        selected_type = self.optimization_type_var.get()
        if selected_type == "Maximize/Minimize":
            self.curve_fit_settings.pack_forget()
            self.max_min_settings.pack(fill=tk.BOTH, expand=True)
        elif selected_type == "Curve Fit":
            self.max_min_settings.pack_forget()
            self.curve_fit_settings.pack(fill=tk.BOTH, expand=True)

    def open_add_constraint_window(self):
        dialog = AddConstraintDialog(
            self, self.selected_parameters, self.node_voltage_expressions
        )
        self.wait_window(dialog)
        if dialog.constraint:
            self.add_constraint(dialog.constraint)

    def _determine_constraint_type(self, left_expression: str) -> Optional[str]:
        """Determines if the left side is a parameter or node expression."""
        if left_expression in (self.selected_parameters or []):
            return "parameter"
        elif (
            left_expression in self.node_voltage_expressions
        ):  # Add checks for other node types if needed
            return "node"
        else:
            # Could potentially be a more complex expression, but we're simplifying
            # Check if it's *only* a known parameter or node expression
            # You might need more robust parsing if left side can be complex later
            is_valid_expr, used_vars = ExpressionEvaluator(
                self.all_allowed_validation_vars
            ).validate_expression(left_expression)
            if is_valid_expr and len(used_vars) == 1:
                if used_vars[0] in (self.selected_parameters or []):
                    return "parameter"
                if used_vars[0] in self.node_voltage_expressions:
                    return "node"
            return None  # Indicates an invalid or unsupported left-hand side format

    def add_constraint(self, constraint_data: Dict[str, str]):
        """Adds the constraint type and stores it."""
        left_side = constraint_data.get("left", "")
        constraint_type = self._determine_constraint_type(left_side)

        if constraint_type is None:
            messagebox.showerror(
                "Error Adding Constraint",
                f"Invalid left-hand side expression: '{left_side}'. Must be a single selected parameter or node expression (e.g., V(node)).",
            )
            return

        # Add the type to the dictionary
        constraint_data["type"] = constraint_type

        self.constraints.append(constraint_data)  # Store the constraint with its type
        print(f"Added Constraint: {constraint_data}")  # Debug
        # Modify constraint_table.add_constraint to accept and potentially display the type
        self.constraint_table.add_constraint(constraint_data)

    def open_edit_constraint_dialog(self, constraint: Dict[str, str], index: int):
        dialog = EditConstraintDialog(
            self, self.selected_parameters, self.node_voltage_expressions, constraint
        )
        self.wait_window(dialog)  # Wait for dialog to close
        if dialog.constraint is not None:
            new_constraint = (
                dialog.constraint
            )  # Assume EditDialog updated its self.constraint
            constraint_type = self._determine_constraint_type(new_constraint["left"])
            if constraint_type is None:
                messagebox.showerror(
                    "Error", f"Invalid left-hand side: {new_constraint['left']}"
                )
                return
            new_constraint["type"] = constraint_type  # Add/Update type
            self.constraints[index] = new_constraint
            self.constraint_table.update_constraint(
                index, new_constraint
            )  # Update table (needs type support)

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
        # --- Get all constraints (they now include the 'type' key) ---
        all_constraints = (
            self.constraints
        )  # List of dicts like {'left': 'R1', ..., 'type': 'parameter'}

        # --- Separate constraints by type ---
        parameter_constraints = [
            c for c in all_constraints if c.get("type") == "parameter"
        ]
        node_constraints_from_ui = [
            c for c in all_constraints if c.get("type") == "node"
        ]
        untyped_constraints = [
            c for c in all_constraints if c.get("type") not in ["parameter", "node"]
        ]

        print(f"Found {len(parameter_constraints)} parameter constraints:")
        # for pc in parameter_constraints: print(f"  {pc}")
        print(f"Found {len(node_constraints_from_ui)} node constraints:")
        # for nc in node_constraints_from_ui: print(f"  {nc}")
        if untyped_constraints:
            print(
                f"Warning: Found {len(untyped_constraints)} constraints without a valid type."
            )
        optimization_settings = {
            "optimization_type": self.optimization_type_var.get(),
            "constraints": self.constraints,
        }
        if self.optimization_type_var.get() == "Maximize/Minimize":
            optimization_settings.update(self.max_min_settings.get_settings())
        elif self.optimization_type_var.get() == "Curve Fit":
            optimization_settings.update(self.curve_fit_settings.get_settings())

        self.controller.update_app_data("optimization_settings", optimization_settings)

        # SET VARIABLES FOR OPTIMIZATION
        curveData = self.controller.get_app_data("optimization_settings")
        print(f"curveData = {curveData}")
        # Replace with self.controller.get_app_data("optimization_settings) stuff
        TARGET_VALUE = curveData["y_parameter"]
        TEST_ROWS = self.controller.get_app_data("generated_data")
        ORIG_NETLIST_PATH = self.controller.get_app_data("netlist_path")
        NETLIST = self.controller.get_app_data("netlist_object")
        WRITABLE_NETLIST_PATH = ORIG_NETLIST_PATH[:-4] + "Copy.txt"
        # NODE CONSTRAINTS NOT IMPLENTED RN
        NODE_CONSTRAINTS = {}

        print(f"TARGET_VALUE = {TARGET_VALUE}")
        print(f"ORIG_NETLIST_PATH = {ORIG_NETLIST_PATH}")
        print(f"NETLIST.components = {NETLIST.components}")
        print(f"NETLIST.file_path = {NETLIST.file_path}")
        print(f"WRIITABLE_NETLIST_PATH = {WRITABLE_NETLIST_PATH}")

        # UPDATE NETLIST BASED ON OPTIMIZATION SETTINGS AND CONSTRAINTS
        for component in NETLIST.components:
            if component.name in self.controller.get_app_data("selected_parameters"):
                component.variable = True

        # ADD IN INITIAL CONSTRAINTS TO NETLIST CLASS VIA MINVAL MAXVAL
        self.add_part_constraints(curveData["constraints"], NETLIST)

        # Function call for writing proper commands to copy netlist here I think (Joseph's stuff)
        endValue = max([sublist[0] for sublist in TEST_ROWS])
        initValue = min([sublist[0] for sublist in TEST_ROWS])
        shutil.copyfile(NETLIST.file_path, WRITABLE_NETLIST_PATH)
        NETLIST.class_to_file(WRITABLE_NETLIST_PATH)
        NETLIST.writeTranCmdsToFile(
            WRITABLE_NETLIST_PATH,
            (endValue - initValue) / 100,
            endValue,
            initValue,
            (endValue - initValue) / 100,
            TARGET_VALUE,
        )
        # Optimization Call
        optim = curvefit_optimize(
            TARGET_VALUE, TEST_ROWS, NETLIST, WRITABLE_NETLIST_PATH, NODE_CONSTRAINTS
        )
        # print(type(optim))

        # Update AppData
        self.controller.update_app_data("netlist_object", NETLIST)
        self.controller.update_app_data("optimization_results", optim)
        print(f"Optimization Results: {optim}")
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

    def add_part_constraints(self, constraints, netlist):
        def simplify_symbols(symbols):
            if not symbols:
                return []

            simplified = [symbols[0]]  # Start with the first symbol

            for i in range(1, len(symbols)):
                if simplified[-1] == "-" and symbols[i] == "-":
                    simplified[-1] = "+"  # "--" becomes "+"
                elif (simplified[-1] == "+" and symbols[i] == "-") or (
                    simplified[-1] == "-" and symbols[i] == "+"
                ):
                    simplified[-1] = "-"  # "+-" or "-+" becomes "-"
                else:
                    simplified.append(symbols[i])  # Otherwise, keep the symbol
            return simplified

        # Current Approach: In the event of complex constraint (For example R1 + R2 >= R3 + R4) manipulate all minVal and maxVals to min and max solutions.
        # For example, R1's minVal = R3 + R4 - R2. R2's minVal = R3 + R4 - R1. R3's maxVal = R1 + R2 - R4. R4's maxVal = R1 + R2 - R3.
        # Not certain if this is the correct way to do so as it could cause incorrect functioning???
        for constraint in constraints:
            # Parse out  components
            left = (
                constraint["left"]
                .replace("+", " + ")
                .replace("-", " - ")
                .replace("*", " * ")
                .replace("/", " / ")
            )
            right = (
                constraint["right"]
                .replace("+", " + ")
                .replace("-", " - ")
                .replace("*", " * ")
                .replace("/", " / ")
            )

            # Split to components and symbols
            left = left.strip().split()
            right = right.strip().split()

            # Simplify symbols (- , - ==> + or +,- ==> - or -,+ ==> -)
            preppedLeft = simplify_symbols(left)
            preppedRight = simplify_symbols(right)
            print(f"Constraint Left piece: {left}")
            print(f"Constraint Right piece: {right}")
            print(f"Constraint Prepped Left piece: {preppedLeft}")
            print(f"Constraint Prepped Right piece: {preppedRight}")

            # TODO Maybe Put in terms of all positives (e.g. R1 - R2 >= R3 becomes R1 >= R3 + R2)

            # TODO Set minVal and maxVals to min and max solutions. Use evaluator possibly.

            match constraint["operator"]:
                case ">=":
                    # Set minVals of right
                    print(constraint["operator"])
                case "=":
                    print(constraint["operator"])
                case "<=":
                    print(constraint["operator"])
