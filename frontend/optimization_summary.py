import tkinter as tk
from tkinter import ttk
import multiprocessing as mp
from backend.optimzation_process import optimizeProcess

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class OptimizationSummary(tk.Frame):

    def __init__(self, parent: tk.Tk, controller: "AppController"):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        self.parent.title("Optimization In Progress")
        self.pack(fill=tk.BOTH, expand=True)

        # Main frame for centering content
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill=tk.BOTH)
        complete_label = ttk.Label(main_frame, text="Optimization In Progress", font=("Arial", 16, "bold"))
        complete_label.grid(row=0, column=0, pady=20, padx=20, sticky="nsew")

        self.tree = ttk.Treeview(main_frame, columns=("Parameter", "Value"), show="headings")
        self.tree.heading("Parameter", text="Parameter")
        self.tree.heading("Value", text="Value")
        self.tree.column("Parameter", anchor="w", width=200)
        self.tree.column("Value", anchor="w", width=150)
        self.tree.grid(row=1, column=0, pady=10, padx=20, sticky="nsew")

        curveData = self.controller.get_app_data("optimization_settings")
        testRows = self.controller.get_app_data("generated_data")
        netlistPath = self.controller.get_app_data("netlist_path")
        netlistObject = self.controller.get_app_data("netlist_object")
        selectedParameters = self.controller.get_app_data("selected_parameters")

        self.figure = Figure(figsize=(5, 2), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Optimization Progress")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel(f"{curveData["y_parameter"]}")
        self.line, = self.ax.plot([], [])  

        self.canvas = FigureCanvasTkAgg(self.figure, master=main_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=2, column=0, pady=10, padx=20, sticky="nsew")

        self.continue_button = ttk.Button(main_frame, text="Close", command=self.close_window)
        self.continue_button.grid(row=3, column=0, pady=20, padx=20)

        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        


        self.queue = mp.Queue()
        self.process = mp.Process(
            target=optimizeProcess,
            args=(self.queue, curveData, testRows, netlistPath, netlistObject, selectedParameters)
        )
        self.process.start()

        self.update_ui()

    def update_ui(self):
        try:
            while not self.queue.empty():
                msg_type, msg_value = self.queue.get_nowait()
                if msg_type == "Update":
                    self.tree.insert("", 0, values=("Update:", msg_value))
                elif msg_type == "Done":
                    self.tree.insert("", 0, values=("Optimization Completed", msg_value))
                    return
                elif msg_type == "Failed":
                    self.tree.insert("", 0, values=("Optimization Failed", msg_value))
                elif msg_type == "UpdateNetlist":
                    self.controller.update_app_data("netlist_object", msg_value)
                elif msg_type == "UpdateOptimizationResults":
                    self.controller.update_app_data("optimization_results", msg_value)
                elif msg_type == "UpdateYData":
                    self.update_graph(msg_value)  
        except Exception as e:
            print("UI Update Error:", e)

        self.parent.after(10, self.update_ui)

    def update_graph(self, y_data):
        y_data = list(y_data)
        if isinstance(y_data, list):
            x_data = list(range(1, len(y_data) + 1))
            self.line.set_data(x_data, y_data)
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()

    def close_window(self):
        if self.process.is_alive():
            self.process.terminate()
        self.parent.quit()
