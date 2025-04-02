import tkinter as tk
from tkinter import ttk, filedialog
from typing import List, Dict, Any
from .expression_dialog import ExpressionDialog
import numpy as np
import csv
from enum import Enum

class input_type(Enum):
    LINE = 1
    HEAVISIDE = 2
    UPLOAD = 3

class CurveFitSettings(tk.Frame):
    def __init__(self, parent: tk.Frame, parameters: List[str], nodes, controller: "AppController"):
        super().__init__(parent)
        self.controller = controller
        self.parameters = parameters
        self.nodes = nodes
        self.x_parameter_expression_var = tk.StringVar()
        self.y_parameter_expression_var = tk.StringVar()
        self.frames = {}
        self.generated_data = None

        
        # --- combobox for: line input vs heavyside vs custom csv
        self.select_input_type_frame = ttk.Frame(self)
        self.select_input_type_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(self.select_input_type_frame, text="Input Function Type: ").pack(side=tk.LEFT)
        answer = tk.StringVar()
        self.input_type_options = ttk.Combobox(self.select_input_type_frame, textvariable=answer)
        self.input_type_options['values'] = ('Line',
                                        'Heaviside',
                                        'Upload')
        self.input_type_options.pack(side=tk.LEFT)
        if self.input_type_options['values']:
            self.input_type_options.current(0)
        self.input_type_options.bind("<<ComboboxSelected>>", lambda event: self.show_frame())

        self.frames['Line'] = self.create_line_frame()
        self.frames['Heaviside'] = self.create_heaviside_frame()
        self.frames['Upload'] = self.create_upload_frame()

        for frame in self.frames.values():
            frame.pack_forget()

        self.see_inputted_functions = ttk.Frame(self)
        self.see_inputted_functions.pack(pady=5, side=tk.TOP, expand=False)




        # --- X and Y Parameter Dropdowns and Expressions ---
        x_param_label = ttk.Label(self, text="X Parameter: TIME , ")
        x_param_label.pack(side=tk.LEFT)
        self.x_parameter_var = tk.StringVar(value="TIME")
        # x_param_frame = ttk.Frame(self)
        # self.x_parameter_dropdown = ttk.Combobox(
        #     x_param_frame,
        #     textvariable=self.x_parameter_var,
        #     values=["time"],  # Corrected to "time"
        #     state="readonly",
        # )
        # self.x_parameter_dropdown.pack(side=tk.LEFT, padx=5)
        # self.x_parameter_dropdown.bind(
        #     "<<ComboboxSelected>>", self.on_x_parameter_selected
        # )
        # x_expression_button = ttk.Button(
        #     x_param_frame,
        #     text="Expr...",
        #     command=lambda: self.open_expression_dialog(is_x=True),
        # )
        # x_expression_button.pack(side=tk.LEFT)
        # x_param_frame.pack(side=tk.LEFT, padx=5)

        y_param_label = ttk.Label(self, text="Y Parameter:")
        y_param_label.pack(side=tk.LEFT)
        self.y_parameter_var = tk.StringVar()

        y_param_frame = ttk.Frame(self)
        self.y_parameter_dropdown = ttk.Combobox(
            y_param_frame,
            textvariable=self.y_parameter_var,
            values=[f"V({node})" for node in self.nodes],  # Use node voltages
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
        y_param_frame.pack(side=tk.LEFT)
    
    def create_line_frame(self):
        line_frame = tk.Frame(self.select_input_type_frame)
        line_frame.pack()
        tk.Label(line_frame, text="Slope = ").pack(side=tk.LEFT) 
        line_slope = tk.Entry(line_frame, width=5)
        line_slope.pack(side=tk.LEFT)# have to separate the pack() into a new line bc it makes the type NONE
        tk.Label(line_frame, text=", Y-intercept = ").pack(side=tk.LEFT) 
        line_intercept = tk.Entry(line_frame, width=5)
        line_intercept.pack(side=tk.LEFT)
        tk.Label(line_frame, text=", From x = ").pack(side=tk.LEFT)
        line_start_x = tk.Entry(line_frame, width=5)
        line_start_x.pack(side=tk.LEFT)
        tk.Label(line_frame, text="to x = ").pack(side=tk.LEFT)
        line_end_x = tk.Entry(line_frame, width=5)
        line_end_x.pack(side=tk.LEFT)
        self.line_button = tk.Button(line_frame, text="Add Line", command=lambda: self.add_function(input_type.LINE, line_slope, line_intercept, line_start_x, line_end_x))
        self.line_button.pack(side=tk.LEFT, padx=10)
        self.custom_functions = []

        return line_frame

    def create_heaviside_frame(self):
        heaviside_frame = tk.Frame(self.select_input_type_frame)
        heaviside_frame.pack()
        tk.Label(heaviside_frame, text="Amplitude = ").pack(side=tk.LEFT) 
        heaviside_amplitude = tk.Entry(heaviside_frame, width=5)
        heaviside_amplitude.pack(side=tk.LEFT)# have to separate the pack() into a new line bc it makes the type NONE
        tk.Label(heaviside_frame, text=", From x = ").pack(side=tk.LEFT)
        heaviside_start_x = tk.Entry(heaviside_frame, width=5)
        heaviside_start_x.pack(side=tk.LEFT)
        tk.Label(heaviside_frame, text="to x = ").pack(side=tk.LEFT)
        heaviside_end_x = tk.Entry(heaviside_frame, width=5)
        heaviside_end_x.pack(side=tk.LEFT)
        self.heaviside_button = tk.Button(heaviside_frame, text="Add Heaviside", command=lambda:
                   self.add_function(input_type.HEAVISIDE, heaviside_amplitude, heaviside_start_x, heaviside_end_x,""))
        self.heaviside_button.pack(side=tk.LEFT, padx=10)
        
        return heaviside_frame

    def create_upload_frame(self):
        # --- Curve Fit File Picker ---
        upload_frame = tk.Frame(self.select_input_type_frame)
        upload_frame.pack()
        curve_fit_button = tk.Button(upload_frame, text="Select Curve File", command=self.select_curve_file_and_process)
        curve_fit_button.pack(side=tk.LEFT, padx=10)

        self.curve_file_path_var = tk.StringVar(value="")
        curve_file_label = tk.Label(upload_frame, textvariable=self.curve_file_path_var)
        curve_file_label.pack()

        return upload_frame

    def show_frame(self):
        selected_frame = self.input_type_options.get()
        if selected_frame in self.frames:
            # hide all the frames first
            for frame in self.frames.values():
                frame.pack_forget()
            # but show the selected frame
            self.frames[selected_frame].pack(fill=tk.BOTH)

    def clear_existing_data(self):
        self.custom_functions = []
        self.generated_data = None
        
        # Clear the see_inputted_functions frame
        for widget in self.see_inputted_functions.winfo_children():
            widget.destroy()
        
        # Reset the buttons
        self.line_button.config(state=tk.NORMAL)
        self.heaviside_button.config(state=tk.NORMAL)

        
    def add_function(self, in_type, arg1, arg2, arg3, arg4):
        if in_type == input_type.LINE:
            slope = float(arg1.get())
            y_int = float(arg2.get())
            x_start = float(arg3.get())
            x_end = float(arg4.get())
            
            self.heaviside_button.config(state=tk.DISABLED) #disable the other button
            self.custom_functions.append((slope, y_int, x_start, x_end))
            string_func = f"LINE: y = ({slope})*x + {y_int}; from x = [{x_start} to {x_end}]"

            x_values = np.linspace(x_start, x_end, 100)
            y_values = slope * x_values + y_int
            self.generated_data = [[float(x), float(y)] for x, y in zip(x_values, y_values)]
            self.controller.update_app_data("generated_data", self.generated_data)
            # print("Generated LINE data:", self.generated_data)

        elif in_type == input_type.HEAVISIDE:
            amplitude = float(arg1.get())
            x_start = float(arg2.get())
            x_end = float(arg3.get())
            
            self.line_button.config(state=tk.DISABLED) #disable the other button
            self.custom_functions.append((amplitude, x_start, x_end))
            string_func = f"HEAVISIDE: amplitude = {amplitude}; from x = [{x_start} to {x_end}]"
            
            x_values = np.linspace(x_start, x_end, 100)
            y_values = [amplitude if x >= x_start else 0 for x in x_values]
            self.generated_data = [[float(x), float(y)] for x, y in zip(x_values, y_values)]
            self.controller.update_app_data("generated_data", self.generated_data)
            # print("Generated HEAVISIDE data:", self.generated_data)

        else:
            return # this function should never be called if the type was anything other than LINE or HEAVISIDE (i.e. it could not be called if type was UPLOAD)
        self.func_label = ttk.Label(self.see_inputted_functions, text=string_func)
        self.func_label.pack(side=tk.TOP, pady=5)
       


    def select_curve_file_and_process(self):
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
            self.clear_existing_data()
            self.curve_file_path_var.set(file_path)
            self.process_csv_file(file_path)

    def process_csv_file(self, file_path):
        try:
            data_points = []
            with open(file_path, 'r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    # this is assuming CSV is formatted as x,y
                    try:
                        x, y = map(float, row)  # Convert x and y to float
                        data_points.append([x, y])
                    except ValueError:
                        print(f"Skipping row: {row} - Invalid data format")
                        continue 
            self.controller.update_app_data("generated_data", data_points)
            # self.generated_data = data_points  
            # print("Uploaded data:", self.uploaded_data)
            # self.plot_data() #refresh plot w data, if we actually wanna plot
            # use the data_points list for further processing or plotting
        except FileNotFoundError:
            print("File not found.")
        except Exception as e:
            print(f"Error processing CSV file: {e}")

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
        settings = {
            "curve_file": self.curve_file_path_var.get(),
        }
        if self.x_parameter_expression_var.get():
            settings["x_parameter_expression"] = self.x_parameter_expression_var.get()
        else:
            settings["x_parameter"] = self.x_parameter_var.get()

        if self.y_parameter_expression_var.get():
            settings["y_parameter_expression"] = self.y_parameter_expression_var.get()
        else:
            settings["y_parameter"] = self.y_parameter_var.get()
        return settings
