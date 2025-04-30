# XycLOps: A Xyce-Linked Circuit Optimizer

Xyclops is a software tool designed to perform circuit optimization by interfacing with the [Xyce Parallel Electronic Simulator](https://xyce.sandia.gov/). It aims to automate and streamline the process of finding optimal circuit parameters based on specified goals and constraints.

This project is developed as part of the CSCE 483 Capstone course at Texas A&M University, Spring 2025.

## Table of Contents

* [About Xyclops](#about-xyclops)
* [Features](#features)
* [Requirements](#requirements)
* [Installation & Setup](#installation--setup)
  * [Cloning the Repository](#cloning-the-repository)
  * [Setting up the Python Virtual Environment](#setting-up-the-python-virtual-environment)
    * [macOS / Linux](#macos--linux)
    * [Windows](#windows)
  * [Installing Dependencies](#installing-dependencies)
  * [Xyce Setup](#xyce-setup)
* [Usage](#usage)
* [Configuration](#configuration)

## About XycLOps

XycLOps is a GUI for circuit optimization, calling an existing Xyce binary on a user's system. A netlist can be provided, constraints can be set, and certain voltages in the circuit can be optimized to desired curves.

## Features

* Interfaces directly with the Xyce circuit simulator.
* Provides tools for defining optimization goals and constraints.
* [List other key features, e.g., Parameter sweeping, Specific optimization algorithms implemented, GUI for interaction, Results visualization, Support for specific netlist formats]
* Frontend interface for user interaction (launched via `frontend.main`).

## Requirements

* **Python:** Version 3.8+ (Check `requirements.txt` or specify exact version if critical).
* **Pip:** Python package installer (usually comes with Python).
* **Git:** For cloning the repository.
* **Xyce:** The [Xyce Parallel Electronic Simulator](https://xyce.sandia.gov/) must be installed separately. Xyclops needs to be able to execute Xyce simulations.

## Installation & Setup

### Cloning the Repository

```bash
git clone <your-repository-url> # Replace with your actual repo URL
cd xyclops
```

Setting up the Python Virtual Environment
Using a virtual environment (venv) is strongly recommended to manage project dependencies and avoid conflicts with system-wide packages.

### macOS / Linux

1. Create the virtual environment:
Open your terminal in the project's root directory (xyclops) and run:

```
python3 -m venv venv
# If python3 is not available, try: python -m venv venv
```

This creates a directory named venv containing the Python interpreter and libraries.

1. Activate the virtual environment

```
source venv/bin/activate
```

Your terminal prompt should now indicate that you are in the (venv) environment.

### Windows

1. Create the virtual environment:
Open Command Prompt or PowerShell in the project's root directory (xyclops) and run:

```
python -m venv venv
```

This creates a directory named venv.

1. Activate the virtual environment:

* **Using Command Prompt (cmd.exe):**

```
.\venv\Scripts\activate
```

* Using PowerShell:

```
.\venv\Scripts\Activate.ps1
```

Note: If you get an error about script execution being disabled in PowerShell, you may need to temporarily change the execution policy for the current process:

```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

Your terminal prompt should now indicate that you are in the (venv) environment.

## Installing Dependencies

Once your virtual environment is activated (for any OS), install the required Python packages:

```
pip install -r requirements.txt
```

## Xyce Setup

1. Install Xyce: Follow the official installation instructions for your operating system from the Xyce website or documentation.
1. Ensure Xyce is Accessible: Xyclops needs to be able to call the Xyce executable. The easiest way is often to ensure the directory containing the Xyce binary is included in your system's PATH environment variable. Alternatively, you might need to configure the path to the Xyce executable within Xyclops itself (see Configuration).

## Usage

1. Activate the Virtual Environment: If it's not already active, navigate to the project directory and activate the venv using the OS-specific commands above.
1. Run Xyclops: Launch the application (assuming the frontend is the primary interface):

```
python -m frontend.main
```

1. Deactivate the Virtual Environment (When Done):
Simply run the following command in your terminal:

```
deactivate
```

Use code with caution.
Bash

## Configuration

Xyce Path: Ensure that the Xyce binary is within the PATH of your system
