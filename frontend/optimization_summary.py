import tkinter as tk
from tkinter import ttk

# from .app_controller import AppController  # <- REMOVE THIS LINE

class OptimizationSummary(tk.Frame):
    def __init__(        self, parent: tk.Tk, controller: "AppController"
    ):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        self.parent.title("Optimization Complete")
        self.pack(fill=tk.BOTH, expand=True)

        # Label to display the message
        self.complete_label = ttk.Label(self, text="Optimization Complete", font=("Arial", 16))
        self.complete_label.pack(pady=50)

         # Display optimization details
        ttk.Label(self, text=f"Xyce Runs: {self.controller.get_app_data("optimization_results")[0]}").pack(anchor="w")
        ttk.Label(self, text=f"Least Squares Iterations: {self.controller.get_app_data("optimization_results")[1]}").pack(anchor="w")
        ttk.Label(self, text=f"Initial Cost: {self.controller.get_app_data("optimization_results")[2]}").pack(anchor="w")
        ttk.Label(self, text=f"Final Cost: {self.controller.get_app_data("optimization_results")[3]}").pack(anchor="w")
        ttk.Label(self, text=f"Optimality: {self.controller.get_app_data("optimization_results")[4]}").pack(anchor="w")

        # Add a "Continue" button to close the window
        self.continue_button = ttk.Button(self, text="Close", command=self.close_window)
        self.continue_button.pack(side=tk.BOTTOM, pady=20)

    def close_window(self):
        """Closes the window when the continue button is pressed."""
        self.parent.quit()