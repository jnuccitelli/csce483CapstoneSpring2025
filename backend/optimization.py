import numpy as np
import subprocess
from scipy.optimize import least_squares, OptimizeResult
from scipy.interpolate import interp1d
from typing import List, Tuple, Dict, Any
import csv
import os
import shutil
from .netlist_parse import (  # Import from the backend package
    parse_netlist,
    update_netlist_file,
    NetlistError,
    Component,
    netlist_to_string,
)

# --- Constants ---
XYCE_COMMAND = "Xyce"  # Or the full path to Xyce if it's not in your PATH


# --- Custom Exceptions ---
class XyceError(Exception):
    """Custom exception for Xyce-related errors."""

    pass


class CurveFitError(Exception):
    """Custom exception for curve fitting related errors"""

    pass


# --- Helper Functions ---
def run_xyce(
    netlist_path: str, extra_args: List[str] = None
) -> subprocess.CompletedProcess:
    if not extra_args:
        command = [XYCE_COMMAND, netlist_path]
    else:
        command = [XYCE_COMMAND] + extra_args + [netlist_path]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,  # Don't raise an exception yet
            timeout=30,
        )
        if result.returncode != 0:
            raise XyceError(
                f"Xyce run failed with return code {result.returncode}.\n"
                f"Stdout: {result.stdout}\nStderr: {result.stderr}"
            )
        return result

    except FileNotFoundError:
        raise XyceError(f"Xyce executable not found: {XYCE_COMMAND}")
    except subprocess.TimeoutExpired:
        raise XyceError(f"Xyce run timed out after {result.timeout} seconds.")  # type: ignore
    except Exception as e:
        raise XyceError(f"An unexpected error occurred while running Xyce: {e}")


def parse_xyce_prn_output(prn_filepath: str) -> Tuple[List[str], List[List[float]]]:
    """Parses a Xyce .prn output file, handling the 'End of Xyce' line."""
    try:
        with open(prn_filepath, "r") as csvfile:
            csvreader = csv.reader(csvfile)
            variable_names = next(csvreader)  # Read header row
            data = []
            for row in csvreader:
                float_row = []
                for item in row:
                    try:
                        float_row.append(float(item))
                    except ValueError:
                        pass  # Ignore non-numeric values
                if float_row:
                    data.append(float_row)

        if not data:
            raise XyceError(f"No data rows found in file {prn_filepath}")
        return variable_names, data
    except FileNotFoundError:
        raise XyceError(f"PRN file not found: {prn_filepath}")
    except (ValueError, StopIteration) as e:
        raise XyceError(f"Error parsing PRN file {prn_filepath}: {e}")
    except Exception as e:
        raise XyceError(f"An unexpected error occurred: {e}")


def extract_target_curve_data(
    fields: List[str], rows: List[List[float]], x_var: str, y_var: str
) -> Tuple[np.ndarray, np.ndarray]:
    """Extracts and validates x and y data from the target curve."""
    try:
        x_index = fields.index(x_var)
    except ValueError:
        raise CurveFitError(f"X variable '{x_var}' not found in target curve.")
    try:
        y_index = fields.index(y_var)
    except ValueError:
        raise CurveFitError(f"Y variable '{y_var}' not found in target curve.")

    try:
        x_data = np.array([row[x_index] for row in rows])
        y_data = np.array([row[y_index] for row in rows])
    except (IndexError, ValueError) as e:
        raise CurveFitError(f"Error extracting data: {e}")

    if len(x_data) != len(y_data):
        raise CurveFitError("X and Y data lengths do not match.")
    if len(x_data) < 2:
        raise CurveFitError("Target curve must have at least 2 points.")
    if not np.all(np.diff(x_data) > 0):
        raise CurveFitError("X data must be strictly increasing.")
    return x_data, y_data


def curvefit_optimize(
    target_curve_filepath: str,
    netlist_filepath: str,
    x_var: str,
    y_var: str,
    variable_components: List[str],  # List of component *names*
    max_iterations: int = 100,  # Added max iterations
) -> OptimizeResult:
    # --- 1. Load and Prepare Target Curve ---
    # Check if the target curve file exists
    if not os.path.exists(target_curve_filepath):
        raise FileNotFoundError(f"Target curve file not found: {target_curve_filepath}")
    try:
        with open(target_curve_filepath, "r") as f:
            reader = csv.reader(f)
            target_curve_fields = next(reader)  # Header row
            target_curve_rows = [[float(val) for val in row] for row in reader]
    except Exception as e:
        raise CurveFitError(f"Error reading or parsing target curve file: {e}")
    x_ideal, y_ideal = extract_target_curve_data(
        target_curve_fields, target_curve_rows, x_var, y_var
    )
    ideal_interpolation = interp1d(
        x_ideal,
        y_ideal,
        kind="linear",
        bounds_error=False,
        fill_value=(y_ideal[0], y_ideal[-1]),
    )

    # --- 2. Load and Prepare Netlist ---
    initial_netlist_components, _ = parse_netlist(netlist_filepath)  # Get components
    # Create a dictionary mapping component *names* to their *initial values*.
    initial_values: Dict[str, str] = {
        comp.name: comp.value
        for comp in initial_netlist_components  # Use components
        if comp.name in variable_components
    }
    if not initial_values:
        raise ValueError("No variable components found for optimization.")
    # Create a *temporary* copy of the netlist to work with.
    temp_netlist_filepath = netlist_filepath + ".tmp"
    shutil.copyfile(netlist_filepath, temp_netlist_filepath)

    run_state = {"first_run": True, "master_x_points": np.array([])}

    # --- 3. Define the Residual Function ---
    def residuals(values: List[float]) -> np.ndarray:
        # create a copy of the netlist to work with
        component_objs: List[Component] = []
        for component in initial_netlist_components:  # Use components
            component_objs.append(component)

        if len(initial_values) != len(values):
            raise ValueError(
                "Number of optimization variables does not match the number of variable components"
            )
        # Create a dictionary to map component *names* to *current* values.
        current_values = dict(zip(initial_values.keys(), values))  # type: ignore

        for component in component_objs:
            if component.name in current_values:
                # Directly set the value of the component
                component.value = str(current_values[component.name])  # Just assign!

        update_netlist_file(temp_netlist_filepath, component_objs)

        try:
            result = run_xyce(temp_netlist_filepath, ["-delim", "COMMA"])
            fields, data = parse_xyce_prn_output(temp_netlist_filepath + ".prn")
            x_xyce, y_xyce = extract_target_curve_data(fields, data, "TIME", y_var)

            if run_state["first_run"]:
                run_state["first_run"] = False
                run_state["master_x_points"] = x_xyce

            xyce_interpolation = interp1d(
                x_xyce,
                y_xyce,
                kind="linear",
                bounds_error=False,
                fill_value=(y_xyce[0], y_xyce[-1]),
            )
            ideal_interp_values = ideal_interpolation(run_state["master_x_points"])
            xyce_interp_values = xyce_interpolation(run_state["master_x_points"])
            residuals_array = ideal_interp_values - xyce_interp_values
            return residuals_array

        except (XyceError, NetlistError, CurveFitError) as e:
            print(f"Error during simulation: {e}")
            return np.ones(len(run_state["master_x_points"])) * 1e10

    # --- 4. Run Optimization ---
    initial_values_list = [
        float(x) for x in initial_values.values()
    ]  # Convert to floats
    result = least_squares(
        residuals, initial_values_list, max_nfev=max_iterations
    )  # Pass max iterations

    # --- 5.  Update and return---
    # Get the optimized component values *in the correct order*.
    optimized_component_values = dict(zip(initial_values.keys(), result.x))  # type: ignore

    # Create final list of components
    final_netlist = []
    for comp in initial_netlist_components:  # Use components.
        if comp.name in optimized_component_values:
            # Directly update
            comp.value = str(optimized_component_values[comp.name])
            final_netlist.append(comp)  # Add the updated
        else:
            final_netlist.append(comp)  # Keep original component

    # Write the final netlist to the *original* file (or a separate output file).
    update_netlist_file(netlist_filepath, final_netlist)

    # Clean up the temporary file
    os.remove(temp_netlist_filepath)

    return result
