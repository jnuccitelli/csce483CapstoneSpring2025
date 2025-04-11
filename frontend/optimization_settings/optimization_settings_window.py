import tkinter as tk

from collections import defaultdict
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional
from .add_constraint_dialog import AddConstraintDialog
from .edit_constraint_dialog import EditConstraintDialog
from .expression_dialog import ExpressionDialog
from .constraint_table import ConstraintTable
from .max_min_settings import MaxMinSettings
from .curve_fit_settings import CurveFitSettings
from ..utils import import_constraints_from_file, export_constraints_to_file
from .expression_evaluator import ExpressionEvaluator


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

        self.optimization_types = ["Curve Fit"]  # "Maximize/Minimize",
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

        # # --- Settings Panels (Max/Min and Curve Fit) ---
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
        # self.max_min_settings = MaxMinSettings(setting_panel_frame, self.selected_parameters)
        # self.max_min_settings.pack(fill=tk.X)
        # self.max_min_settings.pack_forget()  # Initially hidden

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
        import_export_frame.pack(side=tk.TOP)  # Corrected row/column

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
        self.continue_button = ttk.Button(
            navigation_frame,
            text="Begin Optimization",
            command=self.go_forward,
            state=tk.DISABLED,
        )
        self.continue_button.pack(side=tk.RIGHT, padx=5)

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

    #     if selected_type == "Maximize/Minimize":
    #         self.curve_fit_settings.pack_forget()
    #         self.max_min_settings.pack(fill=tk.BOTH, expand=True)
    #     elif selected_type == "Curve Fit":
    #         self.max_min_settings.pack_forget()
    #         self.curve_fit_settings.pack(fill=tk.BOTH, expand=True)

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
        """Adds the constraint type, checks for cycles (params & nodes), and stores it."""
        left_side = constraint_data.get("left", "")
        constraint_type = self._determine_constraint_type(left_side)

        if constraint_type is None:
            messagebox.showerror(
                "Error Adding Constraint",
                f"Invalid left-hand side expression: '{left_side}'. Must be a single selected parameter or node expression (e.g., V(node)).",
            )
            return

        constraint_data["type"] = constraint_type  # Add type info

        # --- CYCLE CHECK (Modified Trigger) ---
        # Check cycles if ANY equality constraint is being added
        if constraint_data.get("operator") == "=":  # Check only operator now
            temp_constraints = self.constraints + [constraint_data]
            if self.check_for_constraint_cycles(temp_constraints):
                messagebox.showerror(
                    "Cycle Detected",
                    f"Adding constraint '{constraint_data['left']} {constraint_data['operator']} {constraint_data['right']}' would create a cyclic dependency involving parameters and/or nodes. Please revise.",
                    parent=self,
                )
                return  # Do not add the constraint

        # --- END CYCLE CHECK ---

        self.constraints.append(constraint_data)
        print(f"Added Constraint: {constraint_data}")
        self.constraint_table.add_constraint(constraint_data)

    def open_edit_constraint_dialog(
        self, constraint_to_edit: Dict[str, str], index: int
    ):
        """Opens the Edit dialog and handles the result, including cycle check (params & nodes)."""
        dialog = EditConstraintDialog(
            self,
            self.selected_parameters,
            self.node_voltage_expressions,
            constraint_to_edit.copy(),
        )
        self.wait_window(dialog)

        if dialog.constraint is not None:
            proposed_constraint = dialog.constraint

            # --- VALIDATION and TYPE DETERMINATION ---
            constraint_type = self._determine_constraint_type(
                proposed_constraint["left"]
            )
            if constraint_type is None:
                messagebox.showerror(
                    "Error",
                    f"Invalid left-hand side after edit: {proposed_constraint['left']}",
                )
                return
            proposed_constraint["type"] = constraint_type

            # --- CYCLE CHECK (Modified Trigger) ---
            # Check cycles if ANY equality constraint results from the edit
            if proposed_constraint.get("operator") == "=":  # Check only operator now
                temp_constraints = [
                    c for i, c in enumerate(self.constraints) if i != index
                ] + [proposed_constraint]

                if self.check_for_constraint_cycles(temp_constraints):
                    messagebox.showerror(
                        "Cycle Detected",
                        f"Editing constraint to '{proposed_constraint['left']} {proposed_constraint['operator']} {proposed_constraint['right']}' would create a cyclic dependency involving parameters and/or nodes. Please revise.",
                        parent=self,
                    )
                    return  # Do not apply the edit

            # --- END CYCLE CHECK ---

            # If validation and cycle check pass, apply the changes
            self.constraints[index] = proposed_constraint
            self.constraint_table.update_constraint(index, proposed_constraint)

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

    # The edit_constraint method now just calls the modified open_edit_constraint_dialog
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

        # Get the *current* constraint data from our internal list
        # It's safer than parsing the Treeview again, assuming self.constraints is the source of truth
        if 0 <= index < len(self.constraints):
            current_constraint = self.constraints[index]
            # Call the updated method that handles the dialog and checks
            self.open_edit_constraint_dialog(current_constraint, index)
        else:
            messagebox.showerror("Error", "Could not find selected constraint data.")

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
        # if self.optimization_type_var.get() == "Maximize/Minimize":
        #     optimization_settings.update(self.max_min_settings.get_settings())
        # elif self.optimization_type_var.get() == "Curve Fit":
        optimization_settings.update(self.curve_fit_settings.get_settings())

        self.controller.update_app_data("optimization_settings", optimization_settings)

        ###########################################################################################################################################
        # SET VARIABLES FOR OPTIMIZATION
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
        equalConstraints = []
        for constraint in constraints:
            # Parse out  components
            if constraint["type"] == "parameter":
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
                                print(
                                    f"{component.name} minVal set to {component.minVal}"
                                )
                            case "=":
                                component.value = eval(right, componentVals)
                                component.variable = False
                                component.modified = True
                                equalConstraints.append(constraint)
                                print(f"{component.name} set to {component.value}")
                            case "<=":
                                component.maxVal = eval(right, componentVals)
                                print(
                                    f"{component.name} maxVal set to {component.maxVal}"
                                )
                        break
        return equalConstraints

    def add_node_constraints(self, constraints):
        formattedNodeConstraints = {}
        nodes = {}
        for constraint in constraints:
            if constraint["type"] == "node":
                nodes[constraint["left"].strip()] = [None, None]
        for constraint in constraints:
            if constraint["type"] == "node":
                match constraint["operator"]:
                    case ">=":
                        nodes[constraint["left"].strip()][0] = float(
                            constraint["right"].strip()
                        )
                    case "<=":
                        nodes[constraint["left"].strip()][1] = float(
                            constraint["right"].strip()
                        )
        for node in nodes:
            formattedNodeConstraints[node] = (nodes[node][0], nodes[node][1])
            # left = constraint["left"].strip()
            # right = float(constraint["right"].strip())
            # formattedNodeConstraints[left] = (None,None)
        return formattedNodeConstraints

    def _build_dependency_graph(
        self, constraints_to_consider: List[Dict[str, str]]
    ) -> Dict[str, set]:
        """
        Builds a dependency graph from ALL '=' constraints, including parameters and nodes.
        Nodes in the graph are parameter names (e.g., 'R1') or node expressions (e.g., 'V(1)').
        An edge X -> Y means Y depends on X (e.g., Y = f(X)).
        """
        graph = defaultdict(set)
        # Evaluator needs all potential variables on the RHS
        evaluator = ExpressionEvaluator(
            parameters=self.selected_parameters,
            node_expressions=self.node_voltage_expressions,
        )
        # Define the set of all items that can be nodes in our dependency graph
        all_valid_graph_nodes = set(self.selected_parameters or []) | set(
            self.node_voltage_expressions or []
        )

        for constraint in constraints_to_consider:
            # Consider ALL equality constraints
            if constraint.get("operator") == "=":
                lhs = constraint[
                    "left"
                ]  # This is the dependent item (parameter or node)
                rhs_expr = constraint["right"]

                # Ensure the LHS is a valid parameter or node expression we care about
                if lhs not in all_valid_graph_nodes:
                    continue  # Skip if LHS isn't a parameter or known node

                # Validate the RHS and get the *original* parameters/nodes it uses
                is_valid, rhs_vars_used = evaluator.validate_expression(rhs_expr)

                if is_valid:
                    # Add edges: dependency -> dependent (rhs_var -> lhs)
                    for rhs_var in rhs_vars_used:
                        # Only add edges if the dependency (rhs_var) is also a valid graph node
                        if rhs_var in all_valid_graph_nodes:
                            graph[rhs_var].add(lhs)  # Add edge from rhs_var to lhs
        # print(f"Built Graph: {dict(graph)}") # Debug: See the graph structure
        return graph

    def _detect_cycle_util(
        self, node: str, graph: Dict[str, set], visiting: set, visited: set
    ) -> bool:
        """DFS utility for cycle detection."""
        visiting.add(node)

        for neighbor in graph.get(node, set()):
            if neighbor in visiting:
                return True  # Cycle detected
            if neighbor not in visited:
                if self._detect_cycle_util(neighbor, graph, visiting, visited):
                    return True  # Cycle detected in recursive call

        visiting.remove(node)
        visited.add(node)
        return False

    def check_for_constraint_cycles(
        self, constraints_to_check: List[Dict[str, str]]
    ) -> bool:
        """Checks for cyclic dependencies in a given list of constraints (params and nodes)."""
        graph = self._build_dependency_graph(constraints_to_check)
        visiting = set()
        visited = set()

        # Get all unique nodes present in the graph (both keys and values)
        all_nodes_in_graph = set(graph.keys()) | set(
            n for dependents in graph.values() for n in dependents
        )

        for node in all_nodes_in_graph:
            if node not in visited:
                if self._detect_cycle_util(node, graph, visiting, visited):
                    # print(f"Cycle detected involving node: {node}") # Debug
                    return True  # Cycle found

        return False  # No cycles found
