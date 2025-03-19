# main.py (in circuit_optimizer directory)
import tkinter as tk
from frontend.app_controller import AppController  # Absolute import


def main() -> None:
    root = tk.Tk()
    app = AppController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
