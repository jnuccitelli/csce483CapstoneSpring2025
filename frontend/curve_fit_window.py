import tkinter as tk
from tkinter import ttk, messagebox


# Sample variable options
variables = ["Var1", "Var2", "Var3", "Var4"]

class OptimizationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Xyce Curve Fit Optimization")

        # X and Y Axis Selection
        ttk.Label(root, text="Select X-axis variable:").grid(row=0, column=0, padx=5, pady=5)
        self.x_var = ttk.Combobox(root, values=variables, state="readonly")
        self.x_var.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(root, text="Select Y-axis variable:").grid(row=1, column=0, padx=5, pady=5)
        self.y_var = ttk.Combobox(root, values=variables, state="readonly")
        self.y_var.grid(row=1, column=1, padx=5, pady=5)

        # Horizontal Line Value
        ttk.Label(root, text="Horizontal Line Value:").grid(row=2, column=0, padx=5, pady=5)
        self.h_line_value = ttk.Entry(root)
        self.h_line_value.grid(row=2, column=1, padx=5, pady=5)

        # Max Iterations
        ttk.Label(root, text="Max Iterations:").grid(row=3, column=0, padx=5, pady=5)
        self.max_iter = ttk.Entry(root)
        self.max_iter.grid(row=3, column=1, padx=5, pady=5)

        # Time Limit
        ttk.Label(root, text="Time Limit (seconds):").grid(row=4, column=0, padx=5, pady=5)
        self.time_limit = ttk.Entry(root)
        self.time_limit.grid(row=4, column=1, padx=5, pady=5)

        # Constraint Section
        ttk.Label(root, text="Add Constraints:").grid(row=5, column=0, padx=5, pady=5)
        self.constraint_var = ttk.Combobox(root, values=variables, state="readonly")
        self.constraint_var.grid(row=5, column=1, padx=5, pady=5)

        self.constraint_value = ttk.Entry(root)
        self.constraint_value.grid(row=5, column=2, padx=5, pady=5)

        self.bound_type = tk.StringVar(value="Upper")
        ttk.Radiobutton(root, text="Upper", variable=self.bound_type, value="Upper").grid(row=5, column=3)
        ttk.Radiobutton(root, text="Lower", variable=self.bound_type, value="Lower").grid(row=5, column=4)

        self.add_constraint_btn = ttk.Button(root, text="Add", command=self.add_constraint)
        self.add_constraint_btn.grid(row=5, column=5, padx=5, pady=5)

        # Constraint List
        self.constraints_list = tk.Listbox(root, height=5, width=50)
        self.constraints_list.grid(row=6, column=0, columnspan=6, padx=5, pady=5)

        # Progress Bar
        ttk.Label(root, text="Simulation Progress:").grid(row=7, column=0, padx=5, pady=5)
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=7, column=1, columnspan=3, padx=5, pady=5)

        # Status Label
        self.status_label = ttk.Label(root, text="Waiting for input...")
        self.status_label.grid(row=8, column=0, columnspan=6, pady=5)

        # Back and Continue Buttons
        self.back_btn = ttk.Button(root, text="Back", command=self.go_back)
        self.back_btn.grid(row=9, column=0, padx=5, pady=10)

        self.continue_btn = ttk.Button(root, text="Start Optimization", command=self.start_optimization)
        self.continue_btn.grid(row=9, column=1, padx=5, pady=10)

    def add_constraint(self):
        var = self.constraint_var.get()
        value = self.constraint_value.get()
        bound = self.bound_type.get()

        if var and value:
            self.constraints_list.insert(tk.END, f"{var} {bound} Bound: {value}")
        else:
            messagebox.showwarning("Input Error", "Please select a variable and enter a value.")

    def go_back(self):
        messagebox.showinfo("Back", "Returning to the previous step...")

    def start_optimization(self):
        """ Start the optimization process and update progress. """
        x_axis = self.x_var.get()
        y_axis = self.y_var.get()
        h_line = self.h_line_value.get()
        max_iter = self.max_iter.get()
        time_limit = self.time_limit.get()

        if not x_axis or not y_axis:
            messagebox.showerror("Input Error", "Please select X and Y variables.")
            return

        try:
            max_iter = int(max_iter) if max_iter else None
            time_limit = float(time_limit) if time_limit else None
        except ValueError:
            messagebox.showerror("Input Error", "Max Iterations and Time Limit must be numbers.")
            return

        constraints = [self.constraints_list.get(i) for i in range(self.constraints_list.size())]

        # Disable UI elements while running
        self.continue_btn.config(state="disabled")
        self.status_label.config(text="Running optimization...")
        self.progress["value"] = 0

        # Simulate optimization in steps
        self.simulate_progress(0, max_iter or 100)

    def simulate_progress(self, step, max_steps):
        """ Simulates optimization process by updating progress bar. """
        if step <= max_steps:
            self.progress["value"] = (step / max_steps) * 100
            self.status_label.config(text=f"Running... {step}/{max_steps} simulations completed")
            self.root.after(100, self.simulate_progress, step + 1, max_steps)
        else:
            self.progress["value"] = 100
            self.status_label.config(text="Optimization complete!")
            self.continue_btn.config(state="normal")
            messagebox.showinfo("Optimization Complete", "Curve fitting optimization finished.")

# Run Tkinter App
root = tk.Tk()
app = OptimizationGUI(root)
root.mainloop()

