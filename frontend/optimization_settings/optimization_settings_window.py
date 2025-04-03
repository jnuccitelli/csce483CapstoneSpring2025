import tkinter as tk
import shutil
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
#from .expression_evaluator import ExpressionEvaluator


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
        optimization_type_frame = ttk.Frame(main_frame)
        optimization_type_frame.pack(side=tk.TOP, fill=tk.X)
        optimization_type_label = ttk.Label(optimization_type_frame, text="Optimization Type:")
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
        setting_panel_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        self.curve_fit_settings = CurveFitSettings(setting_panel_frame, self.selected_parameters, self.nodes, controller)
        self.curve_fit_settings.pack(fill=tk.X) # Initial display

        self.max_min_settings = MaxMinSettings(setting_panel_frame, self.selected_parameters)
        self.max_min_settings.pack(fill=tk.X)
        self.max_min_settings.pack_forget()  # Initially hidden

        

        # --- Constraints Table ---
        constraints_frame = ttk.Frame(main_frame)
        constraints_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        constraints_label = ttk.Label(constraints_frame, text="Constraints:")
        constraints_label.pack(side=tk.TOP, anchor=tk.W, pady=5) # Added a label, and constraints are row 2

        self.constraint_table = ConstraintTable(
            constraints_frame,
            self.open_add_constraint_window,  # Pass the *method* as callback
            self.remove_constraint,  # Pass remove_constraint
            self.open_edit_constraint_dialog,  # Pass edit constraint
        )
        self.constraint_table.pack(fill=tk.BOTH, expand=True)

        # --- Add, Remove, and Edit Buttons (within the ConstraintTable) ---
        self.button_frame = ttk.Frame(constraints_frame)  # Create a frame for buttons.
        self.button_frame.pack(side=tk.TOP, anchor=tk.E)
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
        import_export_frame = ttk.Frame(constraints_frame)
        import_export_frame.pack(side=tk.TOP) # Corrected row/column

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
            self.curve_fit_settings.pack_forget()
            self.max_min_settings.pack(fill=tk.BOTH, expand=True)
        elif selected_type == "Curve Fit":
            self.max_min_settings.pack_forget()
            self.curve_fit_settings.pack(fill=tk.BOTH, expand=True)

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

        #SET VARIABLES FOR OPTIMIZATION
        curveData = self.controller.get_app_data("optimization_settings")
        print(f"curveData = {curveData}")
        #Replace with self.controller.get_app_data("optimization_settings) stuff
        TARGET_VALUE = curveData["y_parameter"]
        TEST_ROWS = self.controller.get_app_data("generated_data")
        ORIG_NETLIST_PATH = self.controller.get_app_data("netlist_path")
        NETLIST = self.controller.get_app_data("netlist_object")
        WRITABLE_NETLIST_PATH = ORIG_NETLIST_PATH[:-4]+"Copy.txt"
        #NODE CONSTRAINTS NOT IMPLENTED RN
        NODE_CONSTRAINTS = self.add_node_constraints(curveData["node_constraints"]) #curveData["node_constraints"] does not actually exist yet

        print(f"TARGET_VALUE = {TARGET_VALUE}")
        print(f"ORIG_NETLIST_PATH = {ORIG_NETLIST_PATH}")
        print(f"NETLIST.components = {NETLIST.components}")
        print(f"NETLIST.file_path = {NETLIST.file_path}")
        print(f"WRIITABLE_NETLIST_PATH = {WRITABLE_NETLIST_PATH}")

        #UPDATE NETLIST BASED ON OPTIMIZATION SETTINGS AND CONSTRAINTS
        for component in NETLIST.components:
            if component.name in self.controller.get_app_data("selected_parameters"):
                component.variable = True

        #ADD IN INITIAL CONSTRAINTS TO NETLIST CLASS VIA MINVAL MAXVAL
        EQUALITY_PART_CONSTRAINTS = self.add_part_constraints(curveData["constraints"], NETLIST)
# GET NODE CONSTRAINTS IN THE FORM BRANDON EXPECTING
        #Function call for writing proper commands to copy netlist here I think (Joseph's stuff)
        endValue = max([sublist[0] for sublist in TEST_ROWS])
        initValue = min([sublist[0] for sublist in TEST_ROWS])
        shutil.copyfile(NETLIST.file_path, WRITABLE_NETLIST_PATH)
        NETLIST.class_to_file(WRITABLE_NETLIST_PATH)
        NETLIST.writeTranCmdsToFile(WRITABLE_NETLIST_PATH,(endValue- initValue)/ 100,endValue,initValue,(endValue- initValue)/ 100,TARGET_VALUE)
        #Optimization Call
        optim = curvefit_optimize(TARGET_VALUE, TEST_ROWS, NETLIST, WRITABLE_NETLIST_PATH, NODE_CONSTRAINTS, EQUALITY_PART_CONSTRAINTS)
        # print(type(optim))

        #Update AppData
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

    def add_part_constraints(self,constraints, netlist):
        equalConstraints = []
        for constraint in constraints:
            #Parse out  components
            left = constraint["left"].strip()
            right = constraint["right"].strip()

            componentVals = {}
            for component in netlist.components:
                componentVals[component.name] = component.value
            for component in netlist.components:
                if left == component.name:
                    match constraint["operator"]:
                        case ">=":
                            component.minVal = eval(right, componentVals)
                            print(f"{component.name} minVal set to {component.minVal}")
                        case "=":
                            component.value = eval(right, componentVals)
                            component.variable = False
                            component.modified = True
                            equalConstraints.append(constraint)
                            print(f"{component.name} set to {component.value}")
                        case "<=":
                            component.maxVal = eval(right, componentVals)
                            print(f"{component.name} maxVal set to {component.maxVal}")
                    break
        return equalConstraints
    
    def add_node_constraints(self, constraints):
        formattedNodeConstraints = {}
        nodes = {}
        for constraint in constraints:
            nodes[constraint["left"].strip()] = [None,None]
        for constraint in constraints:
             match constraint["operator"]:
                        case ">=":
                            nodes[constraint["left"].strip()][0] = float(constraint["right"].strip())
                        case "<=":
                            nodes[constraint["left"].strip()][1] = float(constraint["right"].strip())
        for node in nodes:
            formattedNodeConstraints[node] = (nodes[node][0],nodes[node][1])
            #left = constraint["left"].strip()
            #right = float(constraint["right"].strip())
            #formattedNodeConstraints[left] = (None,None)
        return formattedNodeConstraints