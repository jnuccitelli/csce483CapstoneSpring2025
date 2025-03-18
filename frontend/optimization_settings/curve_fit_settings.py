import tkinter as tk
from tkinter import ttk, filedialog
from typing import List, Dict, Any
from .expression_dialog import ExpressionDialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime


class CurveFitSettings(tk.Frame):
    def __init__(self, parent: tk.Frame, parameters: List[str], nodes):
        super().__init__(parent)
        self.parameters = parameters
        self.nodes = nodes
        self.x_parameter_expression_var = tk.StringVar()
        self.y_parameter_expression_var = tk.StringVar()

        # --- Curve Fit File Picker ---
        curve_fit_button = ttk.Button(
            self, text="Select Curve File", command=self.select_curve_file
        )
        curve_fit_button.pack()

        self.curve_file_path_var = tk.StringVar(value="")
        curve_file_label = ttk.Label(self, textvariable=self.curve_file_path_var)
        curve_file_label.pack()



        # --- function input here
        
        self.function_input_frame = ttk.Frame(self)
        self.function_input_frame.pack(fill=tk.X, pady=5)
        ttk.Label(self.function_input_frame, text="y =").pack(side=tk.LEFT)
        self.y_equals_function_input = ttk.Entry(self.function_input_frame, width=5)
        self.y_equals_function_input.pack(side=tk.LEFT)
        ttk.Label(self.function_input_frame, text="from x =").pack(side=tk.LEFT)
        self.x_start = tk.Entry(self.function_input_frame, width=5)
        self.x_start.pack(side=tk.LEFT)
        ttk.Label(self.function_input_frame, text="to x =").pack(side=tk.LEFT)
        self.x_end = tk.Entry(self.function_input_frame, width=5)
        self.x_end.pack(side=tk.LEFT)
        ttk.Button(self.function_input_frame, text="Add Function", command=self.add_function).pack(side=tk.LEFT, padx=10)
        
        self.see_inputted_functions = ttk.Frame(self)
        self.see_inputted_functions.pack(fill=tk.Y, pady=5)

        ttk.Button(self.function_input_frame, text="Plot", command=self.generate_data).pack(side=tk.LEFT, padx=10)

        self.custom_functions = []
        self.generated_csv = None

        # --- plotting from input here
        self.figure, self.ax = plt.subplots()
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.see_inputted_functions)
        # self.canvas.draw()
        self.canvas.get_tk_widget().pack()




        # --- X and Y Parameter Dropdowns and Expressions ---
        x_param_label = ttk.Label(self, text="X Parameter:")
        x_param_label.pack(side=tk.LEFT, padx=5)
        self.x_parameter_var = tk.StringVar()
        x_param_frame = ttk.Frame(self)
        self.x_parameter_dropdown = ttk.Combobox(
            x_param_frame,
            textvariable=self.x_parameter_var,
            values=["t"],
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

        y_param_label = ttk.Label(self, text="Y Parameter:")
        y_param_label.pack(side=tk.LEFT, padx=5)
        self.y_parameter_var = tk.StringVar()

        y_param_frame = ttk.Frame(self)
        self.y_parameter_dropdown = ttk.Combobox(
            y_param_frame,
            textvariable=self.y_parameter_var,
            values=[f"V({node})" for node in self.nodes],
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

    def add_function(self):
        self.custom_functions.append((self.y_equals_function_input.get(), self.x_start.get(), self.x_end.get()))
        string_func = "y = " + self.y_equals_function_input.get() + " from x = [" + self.x_start.get() + " to " + self.x_end.get() + "]\n"
        ttk.Label(self.see_inputted_functions, text=string_func).pack(side=tk.LEFT, pady=10)

    def plot_data(self):
        try:
            self.ax.clear()

            if self.generated_csv is not None:
                # df = pd.DataFrame(self.csv_data)
                df = pd.read_csv(self.generated_csv)
                if df.shape[1] >= 2:  # Check if there are at least 2 columns
                    self.ax.scatter(df.iloc[:,0], df.iloc[:,1])
                #.iloc[] is primarily integer position based (from 0 to length-1 of the axis), but may also be used with a boolean array. -- from pandas website
                else:
                    print("CSV data does not have enough columns for scatter plot")
            # if self.x_start is None or self.x_end is None:
            #     raise ValueError("Start and stop values must not be None")
            
                # y = eval(func)
                for func, x_list, dfx_list in zip(self.all_funcs, self.all_x_lists, self.all_dfx_lists):
                    self.ax.plot(x_list, dfx_list['y'], label=f'y = {func}')
                self.ax.legend()
                self.ax.set_xlabel('x') #placeholder, need to update this
                self.ax.set_ylabel('y') #placeholder, need to update this
            self.canvas.draw()
        except Exception as e:
            print(f"Error during plotting: {e}")
        
        
    def create_csv(self, dfx_list):
        if dfx_list is not None:  # Check if dfx exists before trying to save it
            current_datetime = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            csv_filename = f"{current_datetime}_generated.csv"
            try:
                dfx_list.to_csv(csv_filename, index=False)
                print(f"CSV file successfully created: {csv_filename}")
                return csv_filename
            except Exception as e:
                print(f"Error while creating CSV: {e}")
                return None
        else:
            print("No custom functions to save to CSV")
            return None


    def generate_data(self):
        self.all_funcs = []
        self.all_x_lists = []
        self.all_dfx_lists = []
        self.combined_dfx = pd.DataFrame()

        for func, x_start, x_end in self.custom_functions:
            x = np.linspace(float(x_start), float(x_end), 100) #doing 100 for now, TODO: NEED TO CHANGE THIS PLACEHOLDER PROBABLY
            dfx = pd.DataFrame({'x': x})
            vec_func = np.vectorize(lambda x: eval(func, {'x': x, 'np': np}))
            dfx['y'] = vec_func(x)

            self.all_funcs.append(func)
            self.all_x_lists.append(x)
            self.all_dfx_lists.append(dfx)
            self.combined_dfx = pd.concat([self.combined_dfx, dfx], ignore_index=True)

        self.generated_csv = self.create_csv(self.combined_dfx)
        self.plot_data()
        
        


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

    def open_expression_dialog(self, is_x=False):
        dialog = ExpressionDialog(self, self.parameters)
        self.wait_window(dialog)
        if dialog.expression:
            if is_x:
                self.x_parameter_expression_var.set(dialog.expression)
                self.x_parameter_var.set(f"Expr: {dialog.expression}")
            else:
                self.y_parameter_expression_var.set(dialog.expression)
                self.y_parameter_var.set(f"Expr: {dialog.expression}")

    def on_x_parameter_selected(self, event=None):
        self.x_parameter_expression_var.set("")

    def on_y_parameter_selected(self, event=None):
        self.y_parameter_expression_var.set("")

    def get_settings(self) -> Dict[str, Any]:
        settings = {"curve_file": self.curve_file_path_var.get()}
        if self.x_parameter_expression_var.get():
            settings["x_parameter_expression"] = self.x_parameter_expression_var.get()
        else:
            settings["x_parameter"] = self.x_parameter_var.get()

        if self.y_parameter_expression_var.get():
            settings["y_parameter_expression"] = self.y_parameter_expression_var.get()
        else:
            settings["y_parameter"] = self.y_parameter_var.get()
        return settings
