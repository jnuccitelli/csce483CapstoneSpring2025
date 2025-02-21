import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# from .app_controller import AppController  # REMOVE THIS LINE
from typing import List, Optional


class OptimizationSettingsWindow(tk.Frame):
    def __init__(
        self, parent: tk.Tk, controller: "AppController"
    ):  # Use string annotation
        super().__init__(parent)
        self.controller = controller  # Controller is passed as an argument
        self.selected_parameters = self.controller.get_app_data("selected_parameters")
        self.constraints: List[dict] = []

        # --- Main Layout Frame ---
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Optimization Type Dropdown ---
        optimization_type_label = ttk.Label(main_frame, text="Optimization Type:")
        optimization_type_label.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.optimization_types = ["Maximize/Minimize", "Curve Fit"]
        self.optimization_type_var = tk.StringVar(value="Maximize/Minimize")
        self.optimization_type_dropdown = ttk.Combobox(
            main_frame,
            textvariable=self.optimization_type_var,
            values=self.optimization_types,
            state="readonly",  # Prevent typing in the Combobox
        )
        self.optimization_type_dropdown.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.optimization_type_dropdown.bind(
            "<<ComboboxSelected>>", self.on_optimization_type_change
        )  # Binds action

        # --- Max/Min Toggle (for Maximize/Minimize) ---
        self.max_min_frame = ttk.Frame(main_frame)
        self.max_min_frame.grid(row=0, column=2, sticky=tk.W, pady=5)

        self.max_min_var = tk.StringVar(value="Max")  # Default to Max
        self.max_radio = ttk.Radiobutton(
            self.max_min_frame, text="Max", variable=self.max_min_var, value="Max"
        )
        self.max_radio.pack(side=tk.LEFT)
        self.min_radio = ttk.Radiobutton(
            self.max_min_frame, text="Min", variable=self.max_min_var, value="Min"
        )
        self.min_radio.pack(side=tk.LEFT)

        # --- Parameter Selection Dropdown (for Maximize/Minimize) ---
        parameter_label = ttk.Label(main_frame, text="Parameter:")
        parameter_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        self.parameter_var = tk.StringVar(value="Select Parameter")  # Default value
        self.parameter_dropdown = ttk.Combobox(
            main_frame,
            textvariable=self.parameter_var,
            values=self.selected_parameters,  # Use the selected parameters from AppData
            state="readonly",
        )
        self.parameter_dropdown.grid(row=1, column=1, sticky=tk.W, pady=5)

        # --- Iterations Input (for Max/Min) ---
        iterations_label = ttk.Label(main_frame, text="Max Iterations:")
        iterations_label.grid(row=2, column=0, sticky=tk.W, pady=5)

        self.iterations_var = tk.StringVar(value="100")  # Default value
        self.iterations_entry = ttk.Entry(main_frame, textvariable=self.iterations_var)
        self.iterations_entry.grid(row=2, column=1, sticky=tk.W, pady=5)

        # --- Curve Fit File Picker ---
        self.curve_fit_frame = ttk.Frame(main_frame)  # Use a frame to manage visibility
        # self.curve_fit_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5) #Starts hidden

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

        # --- X and Y Parameter Dropdowns (for Curve Fit) ---
        x_param_label = ttk.Label(self.curve_fit_frame, text="X Parameter:")
        x_param_label.pack(side=tk.LEFT, padx=5)
        self.x_parameter_var = tk.StringVar()
        self.x_parameter_dropdown = ttk.Combobox(
            self.curve_fit_frame,
            textvariable=self.x_parameter_var,
            values=self.selected_parameters,
            state="readonly",
        )
        self.x_parameter_dropdown.pack(side=tk.LEFT, padx=5)

        y_param_label = ttk.Label(self.curve_fit_frame, text="Y Parameter:")
        y_param_label.pack(side=tk.LEFT, padx=5)
        self.y_parameter_var = tk.StringVar()
        self.y_parameter_dropdown = ttk.Combobox(
            self.curve_fit_frame,
            textvariable=self.y_parameter_var,
            values=self.selected_parameters,
            state="readonly",
        )
        self.y_parameter_dropdown.pack(side=tk.LEFT, padx=5)

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
        self.constraints_table.column(
            "Parameter", width=100
        )  # Adjust column widths as needed
        self.constraints_table.column("Type", width=50)
        self.constraints_table.column("Value", width=100)

        # --- Add Constraint Button ---
        add_constraint_button = ttk.Button(
            main_frame, text="Add Constraint", command=self.open_add_constraint_window
        )
        add_constraint_button.grid(
            row=3, column=2, sticky=tk.E, pady=5
        )  # Place it to the right of the label

        # --- Remove Constraint Button ---
        remove_constraint_button = ttk.Button(
            main_frame, text="Remove Constraint", command=self.remove_constraint
        )
        remove_constraint_button.grid(
            row=4, column=2, sticky=tk.NE, pady=5
        )  # Place below "Add"

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
            self.curve_fit_frame.grid_remove()  # Hide curve fit options
            self.max_min_frame.grid()  # Show max/min options
            self.parameter_dropdown.grid()
            self.iterations_entry.grid()
            parameter_label = ttk.Label(self, text="Parameter:")
        elif selected_type == "Curve Fit":
            self.max_min_frame.grid_remove()  # Hide max/min options
            self.parameter_dropdown.grid_remove()
            self.iterations_entry.grid_remove()
            self.curve_fit_frame.grid(
                row=1, column=0, columnspan=3, sticky=tk.W, pady=5
            )  # Show curve fit options

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
            # You'll need to add code here to *read* and process the curve data

    def open_add_constraint_window(self):
        dialog = AddConstraintDialog(
            self, self.selected_parameters
        )  # Pass self and parameters
        # dialog.grab_set() #Removed to prevent blocking
        self.wait_window(
            dialog
        )  # Use wait_window. This waits for the dialog to be destroyed.

        # Get the constraint data from the dialog after it's closed
        if dialog.constraint:  # Check if a constraint was actually added
            self.add_constraint(dialog.constraint)

    def add_constraint(self, constraint: dict):
        """Adds a constraint to the table and the internal list."""
        self.constraints.append(constraint)
        self.constraints_table.insert(
            "",
            tk.END,
            values=(constraint["parameter"], constraint["type"], constraint["value"]),
        )

    def remove_constraint(self):
        """Removes the selected constraint from the table and list."""
        selected_items = self.constraints_table.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a constraint to remove.")
            return

        # Iterate in reverse order to avoid index issues when deleting
        for selected_item in reversed(selected_items):
            # Get the index of the selected item in the Treeview
            index = self.constraints_table.index(selected_item)
            # Delete from both the Treeview and the constraints list
            self.constraints_table.delete(selected_item)
            del self.constraints[index]

    def go_back(self):
        self.controller.navigate(
            "parameter_selection"
        )  # Go back to parameter selection

    def go_forward(self):
        optimization_settings = {
            "optimization_type": self.optimization_type_var.get(),
            "max_min": self.max_min_var.get()
            if self.optimization_type_var.get() == "Maximize/Minimize"
            else None,
            "parameter": self.parameter_var.get()
            if self.optimization_type_var.get() == "Maximize/Minimize"
            else None,
            "iterations": self.iterations_var.get()
            if self.optimization_type_var.get() == "Maximize/Minimize"
            else None,
            "curve_file": self.curve_file_path_var.get()
            if self.optimization_type_var.get() == "Curve Fit"
            else None,
            "x_parameter": self.x_parameter_var.get()
            if self.optimization_type_var.get() == "Curve Fit"
            else None,
            "y_parameter": self.y_parameter_var.get()
            if self.optimization_type_var.get() == "Curve Fit"
            else None,
            "constraints": self.constraints,
        }
        self.controller.update_app_data("optimization_settings", optimization_settings)
        print("Continue to next window (implementation needed)...")  # Placeholder


class AddConstraintDialog(tk.Toplevel):  # Use Toplevel for secondary windows
    def __init__(self, parent, parameters: List[str]):
        super().__init__(parent)
        self.title("Add Constraint")
        self.parameters = parameters
        self.constraint = None  # Store the created constraint here

        # --- Parameter Selection ---
        param_label = ttk.Label(self, text="Variable Limit:")
        param_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.parameter_var = tk.StringVar(value="Select Parameter")
        self.parameter_dropdown = ttk.Combobox(
            self,
            textvariable=self.parameter_var,
            values=self.parameters,
            state="readonly",
        )
        self.parameter_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        # --- Constraint Type and Value ---
        self.constraint_type_var = tk.StringVar(value="=")  # Default to equals
        self.value_var = tk.StringVar()

        equal_radio = ttk.Radiobutton(
            self, text="Equal", variable=self.constraint_type_var, value="="
        )
        equal_radio.grid(row=0, column=2, sticky=tk.W, padx=5)
        lower_radio = ttk.Radiobutton(
            self, text="Lower Bound", variable=self.constraint_type_var, value=">="
        )
        lower_radio.grid(row=0, column=3, sticky=tk.W, padx=5)
        upper_radio = ttk.Radiobutton(
            self, text="Upper Bound", variable=self.constraint_type_var, value="<="
        )
        upper_radio.grid(row=0, column=4, sticky=tk.W, padx=5)

        value_entry = ttk.Entry(self, textvariable=self.value_var)
        value_entry.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)

        # --- OK and Cancel Buttons ---
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=0, columnspan=6, pady=10)

        ok_button = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def on_ok(self):
        # Get the constraint data
        parameter = self.parameter_var.get()
        constraint_type = self.constraint_type_var.get()
        value = self.value_var.get()

        # Validate the input (important!)
        if parameter == "Select Parameter" or not value:
            messagebox.showerror(
                "Error", "Please select a parameter and enter a value."
            )
            return

        try:
            float(value)  # Check if the value is a number
        except ValueError:
            messagebox.showerror("Error", "Invalid value. Please enter a number.")
            return

        # Create the constraint dictionary
        self.constraint = {
            "parameter": parameter,
            "type": constraint_type,
            "value": value,
        }
        self.destroy()  # Close the dialog

    def on_cancel(self):
        self.constraint = None  # Set to None if canceled
        self.destroy()  # Close the dialog
