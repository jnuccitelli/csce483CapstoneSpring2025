import numpy as np
import shutil
import subprocess
from scipy.optimize import least_squares
from scipy.interpolate import interp1d

# TEMPORARY IN HERE FOR DEV PURPOSES
class Component:
    def __init__(self, name="", type="", value=0, variable=False, modified=False):
        self.name = name
        self.type = type
        self.value = value
        self.variable = variable
        self.modified = modified

class Netlist:
    def __init__(self):
        self.components = []
# END TEMPORARY IN HERE FOR DEV PURPOSES


# def curvefit_optimize(target_curve_fields: list, target_curve_rows: list, netlist: Netlist) -> None:
#     # Copy netlist file
#     local_netlist_file = shutil.copyfile(ORIG_NETLIST_PATH, WRITABLE_NETLIST_PATH)
#     # Parse target_curve to figure out what Y value is
#     y_var = target_curve_fields[1]

#     # Parse netlist to figure out which parts are subject to change
#     changing_components = [x for x in netlist.components if x.variable]

#     # TODO LATER: Divy out runs with parts changed and local Netlist objects-> Make a bunch of temporary netlist files with slight changes if we want simultaneous runs

#     # Map netlist -> least squares value
#     netlist_dict = {}

#     # TODO LATER: This changes only one part at a time
#     # TODO: THESE VALUES SET AMOUNT OF ITERATIONS FOR NOW PENDING DESIGN DECISIONS
#     for i in len(changing_components):
#         # TODO LATER: Could add other loop to address multiple changes, but slow?
#         for j in range(0, NUM_RUNS_PER_VAR):
#             new_netlist = netlist
#             new_netlist.components[i].value = new_netlist.components[i].value*((PERCENT_DEVIATION_FROM_START_VALUE/2)*j+1-PERCENT_DEVIATION_FROM_START_VALUE)
#             new_netlist.components[i].modified = True
#             # TODO: Edit netlistCopy file based off of netlist (relies on Aidan)
#             subprocess.run(["Xyce", "-delim", "COMMA", local_netlist_file])
#             # TODO: Parse output file for values (relies on Joseph)
#             # TODO: scipy.optimize.least_squares or curve_fit or hausdorff? (me) (SOLUTION: LINEAR INTERPOLATION, POINTS FROM XYCE ARE KING)
#             # TODO: add {new_netlist : scipy.optimize.least_squares output} to netlist_dict (me)
#             # netlist_dict[new_netlist] = 

#     # See which Xyce output in netlist_dict has lowest LSR
#     optimal_netlist = min(netlist_dict, key=netlist_dict.get)
#     # TODO: Write out optimal_netlist object to file (relies on Aidan)


def curvefit_optimize(target_curve_fields: list, target_curve_rows: list, netlist: Netlist) -> None:
    # TODO: Properly parse correct y_var using below, just x[1] for now
    # # y_var = target_curve_fields[1]
    x_ideal = np.array([x[0] for x in target_curve_rows])
    y_ideal = np.array([x[1] for x in target_curve_rows])
    ideal_interpolation = interp1d(x_ideal, y_ideal)

    # Copy netlist file
    local_netlist_file = shutil.copyfile(ORIG_NETLIST_PATH, WRITABLE_NETLIST_PATH)

    # Parse netlist to figure out which parts are subject to change
    changing_components = [x for x in netlist.components if x.variable]
    changing_components_values = [x.value for x in changing_components]

    def residuals(component_values, components):
        new_netlist = netlist

        subprocess.run(["Xyce", "-delim", "COMMA", local_netlist_file])

        return ideal_interpolation(XARRAYFROMXYCE) - YARRAYFROMXYCE
    
    result = least_squares(residuals, changing_components_values, args=(changing_components))

    for i in len(changing_components):
        changing_components[i].value = result.x[i]

    optimal_netlist = netlist    
    for changed_component in changing_components:
        for netlist_component in optimal_netlist.components:
            if changed_component.name == netlist_component.name:
                netlist_component.value = changed_component.value
                netlist_component.modified = True
                break
    # TODO: Write out optimal_netlist object to file (relies on Aidan)

# TEMPORARY TESTING VALUES
ORIG_NETLIST_PATH = r"C:\Users\User\capstone\csce483CapstoneSpring2025\netlist.txt"
WRITABLE_NETLIST_PATH = r"C:\Users\User\capstone\csce483CapstoneSpring2025\netlistCopy.txt"

TEST_FIELDS = ['Time', 'V(1)']
TEST_ROWS = [[0.00000000e+00, ],
        [4.00000000e-04, ],
        [8.00000000e-04, ],
        [1.20000000e-03, ],
        [1.60000000e-03, ],
        [2.00000000e-03, ]]

TEST_NETLIST = Netlist()
TEST_NETLIST.components.append(Component("R1", "R", 1000, True, False))
TEST_NETLIST.components.append(Component("C1", "C", 0.00000047, True, False))

# THESE VALUES SET AMOUNT OF ITERATIONS FOR NOW PENDING DESIGN DECISIONS
NUM_RUNS_PER_VAR = 5
PERCENT_DEVIATION_FROM_START_VALUE = 0.1
# END TEMPORARY TESTING VALUES

# TEMPORARY
curvefit_optimize(TEST_FIELDS, TEST_ROWS, TEST_NETLIST)
# END TEMPORARY