import tkinter as tk
from tkinter import ttk, messagebox

# sample variable options
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

        # Back and Continue Buttons
        self.back_btn = ttk.Button(root, text="Back", command=self.go_back)
        self.back_btn.grid(row=7, column=0, padx=5, pady=10)

        self.continue_btn = ttk.Button(root, text="Continue", command=self.run_optimization)
        self.continue_btn.grid(row=7, column=1, padx=5, pady=10)

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

    def run_optimization(self):
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

        # call xyce optimization function
        messagebox.showinfo("Optimization Started", f"Running curve fit optimization...\n"
                            f"X-axis: {x_axis}\nY-axis: {y_axis}\n"
                            f"Horizontal Line: {h_line}\n"
                            f"Max Iterations: {max_iter}\nTime Limit: {time_limit}\n"
                            f"Constraints: {constraints}")

# run tkinter App
root = tk.Tk()
app = OptimizationGUI(root)
root.mainloop()
