import numpy as np
import shutil
import subprocess
from scipy.optimize import least_squares
from scipy.interpolate import interp1d
from xyce_parsing_function import parse_xyce_prn_output
from netlist_parse import Netlist

"""
Two constraint types:
1. Node value constraints
    These will be solved by checking output after a Xyce run, then skewing the residual output so it won't select it if the voltage constraint is breached
    This will probably mess up next part value selection if if not done well
2. Part value constraints
    These are simpler to do and can be done using bounds arg of least_squares
    Equation type ones (i.e. R1 + R2 < 4000) are trickier perhaps
"""
# Part Value = Constant
#   TODO (but not really because Not really a case because it would just not be a variable)
# Node Value = Constant
#   TODO
# Part Value <, > Constant
#   TEST by using bounds arg
# Node Value <, > Constant
#   TEST by throwing out/skewing Xyce run output
# Part Value = Equation
#   TODO 
# Node Value = Equation
#   TODO
# Part Value <, > Equation
#   TODO
# Node Value <, > Equation
#   TODO

# TODO: Update Component class with min_value, max_value when constratints are set
"""
node_constraints structure

node_constraints = {
    'V(2)': (None, 5.0),  # Example: V(2) must be <= 5V
    'V(3)': (1.0, None)   # Example: V(3) must be >= 1V
}
"""
def curvefit_optimize(target_value: str, target_curve_rows: list, netlist: Netlist, writable_netlist_path: str, node_constraints: dict) -> None:
    # Assumes input_curve[0] is X, input_curve[1] is Y/target_value
    x_ideal = np.array([x[0] for x in target_curve_rows])
    y_ideal = np.array([x[1] for x in target_curve_rows])
    ideal_interpolation = interp1d(x_ideal, y_ideal)

    # Copy netlist file
    local_netlist_file = shutil.copyfile(netlist.file_path, writable_netlist_path)

    # Parse netlist to figure out which parts are subject to change
    changing_components = [x for x in netlist.components if x.variable]
    changing_components_values = [x.value for x in changing_components]

    lower_bounds = np.array([x.min_value if hasattr(x, "min_value") else -np.inf for x in changing_components])
    upper_bounds = np.array([x.max_value if hasattr(x, "max_value") else np.inf for x in changing_components])


    # print(changing_components_values)
    run_state = {
        "first_run": True,
        "master_x_points": np.array([])
    }
    def residuals(component_values, components):
        new_netlist = netlist
        new_netlist.file_path = local_netlist_file
        # print("TESTING NEW VALUES: ", component_values)
        # Edit new_netlist with correct values
        for i in range(len(component_values)):
            for netlist_component in new_netlist.components:
                if components[i].name == netlist_component.name:
                    netlist_component.value = component_values[i]
                    netlist_component.modified = True
                    break

        # Edit netlistCopy file based off of new_netlist (relies on Aidan)
        new_netlist.class_to_file(local_netlist_file)

        subprocess.run(["Xyce", "-delim", "COMMA", local_netlist_file])


        #TODO: Smart way to set timestep and ensure consistency. Rn just decided arbitrarily by first run
        xyce_parse = parse_xyce_prn_output(local_netlist_file+".prn")

        # Assumes Xyce output is Index, Time, arb. # of VALUES
        row_index = xyce_parse[0].index(target_value)

        X_ARRAY_FROM_XYCE = np.array([float(x[1]) for x in xyce_parse[1]])
        Y_ARRAY_FROM_XYCE = np.array([float(x[row_index]) for x in xyce_parse[1]])
        if run_state["first_run"]:
            run_state["first_run"] = False
            run_state["master_x_points"] = X_ARRAY_FROM_XYCE
        xyce_interpolation = interp1d(X_ARRAY_FROM_XYCE, Y_ARRAY_FROM_XYCE)
        # print("X_ARRAY: ", X_ARRAY_FROM_XYCE)
        # print("Y_ARRAY: ", Y_ARRAY_FROM_XYCE)
        # print("SHAPES: ", X_ARRAY_FROM_XYCE.shape, ideal_interpolation(X_ARRAY_FROM_XYCE).shape, Y_ARRAY_FROM_XYCE.shape, xyce_interpolation(run_state["master_x_points"]).shape)
        # TODO: Proper residual? (subrtarct, rms, etc.)
        # Check node constraint violations
        # TODO: Is an inf penalty appropriate?
        for node_name, (node_lower, node_upper) in node_constraints.items():
            node_index = xyce_parse[0].index(node_name)
            node_values = np.array([float(x[node_index]) for x in xyce_parse[1]])
            if (node_lower is not None and np.any(node_values < node_lower)) or (node_upper is not None and np.any(node_values > node_upper)):
                return np.full_like(run_state["master_x_points"], np.inf)  # Large penalty


        return ideal_interpolation(run_state["master_x_points"]) - xyce_interpolation(run_state["master_x_points"])
    
    # TODO: trf vs dogbox vs lm
    result = least_squares(residuals, changing_components_values, method='lm', bounds=(lower_bounds, upper_bounds), args=(changing_components,))
    # print(result.x)
    for i in range(len(changing_components)):
        changing_components[i].value = result.x[i]

    optimal_netlist = netlist
    optimal_netlist.file_path = local_netlist_file
    for changed_component in changing_components:
        for netlist_component in optimal_netlist.components:
            if changed_component.name == netlist_component.name:
                netlist_component.value = changed_component.value
                netlist_component.modified = True
                break

    optimal_netlist.class_to_file(local_netlist_file)


# WRITABLE_NETLIST_PATH = r"C:\Users\User\capstone\csce483CapstoneSpring2025\netlistCopy.txt"
# TARGET_VALUE = 'V(2)'
# TEST_ROWS = [[0.00000000e+00, 4.00000000e+00],
#         [4.00000000e-04, 4.00000000e+00],
#         [8.00000000e-04, 4.00000000e+00],
#         [1.20000000e-03, 4.00000000e+00],
#         [1.60000000e-03, 4.00000000e+00],
#         [2.00000000e-03, 4.00000000e+00]]
# ORIG_NETLIST_PATH = r"C:\Users\User\capstone\csce483CapstoneSpring2025\netlist.txt"
# TEST_NETLIST = Netlist(ORIG_NETLIST_PATH)
# for component in TEST_NETLIST.components:
#     component.variable = True
# curvefit_optimize(TARGET_VALUE, TEST_ROWS, TEST_NETLIST, WRITABLE_NETLIST_PATH)