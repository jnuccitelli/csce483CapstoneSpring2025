import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any
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

        self.curve_fit_settings = CurveFitSettings(main_frame, self.selected_parameters, self.nodes)
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
        #print(self.controller.get_app_data("optimization_settings"))
        curveData = self.controller.get_app_data("optimization_settings")
        #Replace with self.controller.get_app_data("optimization_settings) stuff
        #TODO Get App data to set variable components to True and the
        TARGET_VALUE = 'V(2)'
        TEST_ROWS = [[0.00000000e+00, 4.00000000e+00],
                [4.00000000e-04, 4.00000000e+00],
                [8.00000000e-04, 4.00000000e+00],
                [1.20000000e-03, 4.00000000e+00],
                [1.60000000e-03, 4.00000000e+00],
                [2.00000000e-03, 4.00000000e+00]]
        ORIG_NETLIST_PATH = self.controller.get_app_data("netlist_path")
        TEST_NETLIST = self.controller.get_app_data("netlist_object")
        print("HELOOOOOSOSODSOD")
        print(TEST_NETLIST)
        WRITABLE_NETLIST_PATH = ORIG_NETLIST_PATH[:-4]+"Copy.txt"
        #ASK Brandon why all true and the node constraints
        for component in TEST_NETLIST.components:
            component.variable = True
        NODE_CONSTRAINTS = {"V(2)":(None, 4.1)}
        NODE_CONSTRAINTS = {}
        optim = curvefit_optimize(TARGET_VALUE, TEST_ROWS, TEST_NETLIST, WRITABLE_NETLIST_PATH, NODE_CONSTRAINTS)
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
