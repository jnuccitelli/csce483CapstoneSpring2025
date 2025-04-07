import tkinter as tk
from tkinter import ttk
import multiprocessing as mp
import time
import shutil
from backend.curvefit_optimization import curvefit_optimize


def optimizeProcess(queue,curveData,testRows,netlistPath,netlistObject,selectedParameters):
    try:
        print("GOT HERE")
        
        print(f"curveData = {curveData}")
        #Replace with self.controller.get_app_data("optimization_settings) stuff
        TARGET_VALUE = curveData["y_parameter"]
        TEST_ROWS = testRows
        ORIG_NETLIST_PATH = netlistPath
        NETLIST = netlistObject
        WRITABLE_NETLIST_PATH = ORIG_NETLIST_PATH[:-4]+"Copy.txt"
        #NODE CONSTRAINTS NOT IMPLENTED RN
        NODE_CONSTRAINTS = {}

        print(f"TARGET_VALUE = {TARGET_VALUE}")
        print(f"ORIG_NETLIST_PATH = {ORIG_NETLIST_PATH}")
        print(f"NETLIST.components = {NETLIST.components}")
        print(f"NETLIST.file_path = {NETLIST.file_path}")
        print(f"WRIITABLE_NETLIST_PATH = {WRITABLE_NETLIST_PATH}")

        #UPDATE NETLIST BASED ON OPTIMIZATION SETTINGS AND CONSTRAINTS
        for component in NETLIST.components:
            if component.name in selectedParameters:
                component.variable = True

        #ADD IN INITIAL CONSTRAINTS TO NETLIST CLASS VIA MINVAL MAXVAL
        #self.add_part_constraints(curveData["constraints"], NETLIST)

        #Function call for writing proper commands to copy netlist here I think (Joseph's stuff)
        endValue = max([sublist[0] for sublist in TEST_ROWS])
        initValue = min([sublist[0] for sublist in TEST_ROWS])
        shutil.copyfile(NETLIST.file_path, WRITABLE_NETLIST_PATH)
        NETLIST.class_to_file(WRITABLE_NETLIST_PATH)
        NETLIST.writeTranCmdsToFile(WRITABLE_NETLIST_PATH,(endValue- initValue)/ 100,endValue,initValue,(endValue- initValue)/ 100,TARGET_VALUE)
        #Optimization Call
        optim = curvefit_optimize(TARGET_VALUE, TEST_ROWS, NETLIST, WRITABLE_NETLIST_PATH, NODE_CONSTRAINTS,queue)
        # print(type(optim))

        #Update AppData
        queue.put(("UpdateNetlist",NETLIST))
        queue.put(("UpdateOptimizationResults",optim))
        
        print(f"Optimization Results: {optim}")
        queue.put(("Update", f"Optimization Results: {optim}"))  
    except:
        queue.put(("Failed","Xyce failed"))


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

        # Label to display the title
        complete_label = ttk.Label(main_frame, text="Optimization In Progress", font=("Arial", 16, "bold"))
        complete_label.grid(row=0, column=0, pady=20, padx=20, sticky="nsew")

        # Treeview for displaying optimization data
        self.tree = ttk.Treeview(main_frame, columns=("Parameter", "Value"), show="headings")
        self.tree.heading("Parameter", text="Parameter")
        self.tree.heading("Value", text="Value")
        self.tree.column("Parameter", anchor="w", width=200)
        self.tree.column("Value", anchor="w", width=150)
        self.tree.grid(row=1, column=0, pady=10, padx=20, sticky="nsew")

        # Add "Close" button below the table
        self.continue_button = ttk.Button(main_frame, text="Close", command=self.close_window)
        self.continue_button.grid(row=2, column=0, pady=20, padx=20)

        # Configure column and row weights for centering
        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=0)
        main_frame.grid_columnconfigure(0, weight=1)

        curveData = self.controller.get_app_data("optimization_settings")
        testRows = self.controller.get_app_data("generated_data")
        netlistPath = self.controller.get_app_data("netlist_path")
        netlistObject = self.controller.get_app_data("netlist_object")
        selectedParameters = self.controller.get_app_data("selected_parameters")

        self.queue = mp.Queue()
        self.process = mp.Process(target=optimizeProcess, args=(self.queue,curveData,testRows, netlistPath,netlistObject,selectedParameters))
        self.process.start()


        self.update_ui()

    def update_ui(self):
        try:
            while not self.queue.empty():
                msg_type, msg_value = self.queue.get_nowait()
                if msg_type == "Update":
                    self.tree.insert("", "end", values=("Update:", msg_value))
                elif msg_type == "Done":
                    self.tree.insert("", "end", values=("Optimzation Completed", msg_value))
                    return  
                elif msg_type == "Failed":
                    self.tree.insert("","end", values=("Optimzation Failed", msg_value))
                elif msg_type == "UpdateNetlist":
                    self.controller.update_app_data("netlist_object", msg_value)
                elif msg_type == "UpdateOptimizationResults":
                    self.controller.update_app_data("optimization_results", msg_value)
        except:
            pass

        self.parent.after(1000, self.update_ui)  

    def close_window(self):
        """Closes the window when the continue button is pressed."""
        if self.process.is_alive():
            self.process.terminate()
        self.parent.quit()
    
    