import tkinter as tk
from tkinter import ttk

class OptimizationSummary(tk.Frame):
    def __init__(self, parent: tk.Tk, controller: "AppController"):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        self.parent.title("Optimization Complete")
        self.pack(fill=tk.BOTH, expand=True)

        # Main frame for centering content
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Label to display the title
        complete_label = ttk.Label(main_frame, text="Optimization Complete", font=("Arial", 16, "bold"))
        complete_label.grid(row=0, column=0, pady=20, padx=20, sticky="nsew")

        # Treeview for displaying optimization data
        self.tree = ttk.Treeview(main_frame, columns=("Parameter", "Value"), show="headings")
        self.tree.heading("Parameter", text="Parameter")
        self.tree.heading("Value", text="Value")
        self.tree.column("Parameter", anchor="w", width=200)
        self.tree.column("Value", anchor="w", width=150)

        # Insert the optimization details into the treeview
        optimization_results = self.controller.get_app_data("optimization_results")
        data = [
            ("Xyce Runs", optimization_results[0]),
            ("Least Squares Iterations", optimization_results[1]),
            ("Initial Cost", optimization_results[2]),
            ("Final Cost", optimization_results[3]),
            ("Optimality", optimization_results[4]),
        ]
        
        for item in data:
            self.tree.insert("", "end", values=item)

        self.tree.grid(row=1, column=0, pady=10, padx=20, sticky="nsew")

        # Add "Continue" button below the table
        self.continue_button = ttk.Button(main_frame, text="Close", command=self.close_window)
        self.continue_button.grid(row=2, column=0, pady=20, padx=20)

        # Configure column and row weights for centering
        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=0)
        main_frame.grid_columnconfigure(0, weight=1)

    def close_window(self):
        """Closes the window when the continue button is pressed."""
        self.parent.quit()