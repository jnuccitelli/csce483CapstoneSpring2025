import numpy as np
import shutil
import subprocess
from scipy.optimize import least_squares
from scipy.interpolate import interp1d

# TEMPORARY IN HERE FOR DEV PURPOSES
import csv

# -> Tuple[List[str], List[List[float]]]
# Delete last line
def parse_xyce_prn_output(prn_filepath: str):
    variable_names = []
    data = []
    with open(prn_filepath, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        variable_names = next(csvreader)
        for row in csvreader:
            data.append(row)
    # Get rid of last line
    data.pop()
    return variable_names, data

class Component:
    def __init__(self, name="", type="", value=0, variable=False, modified=False):
        self.name = name
        self.type = type
        self.value = value
        self.variable = variable
        self.modified = modified

class Netlist:
    def __init__(self, file_name):
        self.components = self.parse_file(file_name)

    def parse_file(self, file_name) -> list:
        components = []
        try:
            with open(file_name,"r") as file:
            #------Parsing Logic------#
            #Current Behavior: Skip Title Line, Commands, and non RLC components
                file.readline()
                for line in file:
                    values=line.strip().split(" ")
                    if(values == [""]):
                        continue
                    if(values[0][0] != "R" and values[0][0] != "L" and values[0][0] != "C"):
                        continue
#####################TODO: Need to deal with component value conversions#####################

                    newComponent = Component(values[0],values[0][0],values[3])
                    components.append(newComponent)
                    print(values)
                    #print(line.strip())
                    #print("Hello")

        except FileNotFoundError:
            print(f"Error: The file '{file_name}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return components
    
    def class_to_file(self, file_name):
        try:
            #Get Current file netlist and modified components in class
            with open(file_name,"r") as file:
                data = file.readlines()
            modifiedComponents = []
            for component in self.components:
                if component.modified == True:
                    modifiedComponents.append(component)
                    component.modified = False
            #print("---------------PRE-CHANGE DATA-----------------")
            #print(data)
            #print("---------------MODIFIED COMPONENTS LIST-----------------")
            #print(modifiedComponents)
            #Generate updated netlist
            updatedData=[]
            for line in data:
                lineData = line.strip().split(" ")
                for component in modifiedComponents:
                    if lineData[0] == component.name:
                        #print("MATCH FOUND!")
                        #print(line)
                        #print(f"LineData[3] = {lineData[3]}")
                        lineData[3] = component.value
                        #print(f"LineData[3] = {lineData[3]}")
                        line = f"{lineData[0]} {lineData[1]} {lineData[2]} {lineData[3]}\n"
                        #print(line)
                        modifiedComponents.remove(component)
                        break
                updatedData.append(line)
            #print("---------------POST-CHANGE DATA-----------------")
            #print(updatedData)
            #print("---------------REMAINING MODIFIED COMPONENTS LIST-----------------")
            #print(modifiedComponents)
            with open(file_name,"w") as file:
                file.writelines(updatedData)
        except FileNotFoundError:
            print(f"Error: The file '{file_name}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
# END TEMPORARY IN HERE FOR DEV PURPOSES


def curvefit_optimize(target_curve_fields: list, target_curve_rows: list, netlist: Netlist) -> None:
    # Assumes second column is time (x[0])
    # TODO: SMART GET INDICES
    row_index = target_curve_fields.index(TARGET_VALUE)
    x_ideal = np.array([x[0] for x in target_curve_rows])
    y_ideal = np.array([x[row_index] for x in target_curve_rows])
    ideal_interpolation = interp1d(x_ideal, y_ideal)

    # Copy netlist file
    local_netlist_file = shutil.copyfile(ORIG_NETLIST_PATH, WRITABLE_NETLIST_PATH)

    # Parse netlist to figure out which parts are subject to change
    changing_components = [x for x in netlist.components if x.variable]
    changing_components_values = [x.value for x in changing_components]
    print(changing_components_values)
    run_state = {
        "first_run": True,
        "master_x_points": np.array([])
    }
    def residuals(component_values, components):
        new_netlist = netlist
        print("TESTING NEW VALUES: ", component_values)
        # Edit new_netlist with correct values
        for i in range(len(component_values)):
            for netlist_component in new_netlist.components:
                if components[i].name == netlist_component.name:
                    netlist_component.value = component_values[i]
                    netlist_component.modified = True
                    break

        # Edit netlistCopy file based off of new_netlist (relies on Aidan)
        new_netlist.class_to_file(local_netlist_file)

        #TODO: SMart way to set timestep and ensure consistency.  Rn hardcoded in file
        subprocess.run(["Xyce", "-delim", "COMMA", local_netlist_file])


        # TODO: MAYBE NOT GOOD, LETTIG FIRST ITERATION SET MASTER X POINTS
        # Parse output file for values into X_ARRAY_FROM_XYCE and Y_ARRAY_FROM_XYCE (relies on someone)
        # NEED TO FORCE XYCE TO DO CERTAIN AMOUNT OF TIMESTEPS
        xyce_parse = parse_xyce_prn_output(local_netlist_file+".prn")
        # TODO: SMART GET INDICES
        X_ARRAY_FROM_XYCE = np.array([float(x[1]) for x in xyce_parse[1]])
        Y_ARRAY_FROM_XYCE = np.array([float(x[2]) for x in xyce_parse[1]])
        if run_state["first_run"]:
            run_state["first_run"] = False
            run_state["master_x_points"] = X_ARRAY_FROM_XYCE
        xyce_interpolation = interp1d(X_ARRAY_FROM_XYCE, Y_ARRAY_FROM_XYCE)
        print("X_ARRAY: ", X_ARRAY_FROM_XYCE)
        print("SHAPES: ", X_ARRAY_FROM_XYCE.shape, ideal_interpolation(X_ARRAY_FROM_XYCE).shape, Y_ARRAY_FROM_XYCE.shape, xyce_interpolation(run_state["master_x_points"]).shape)
        # TODO: Proper residual? (subrtarct, rms, etc.)
        return ideal_interpolation(run_state["master_x_points"]) - xyce_interpolation(run_state["master_x_points"])
    
    result = least_squares(residuals, changing_components_values, method='lm', args=(changing_components,))
    print(result.x)
    for i in range(len(changing_components)):
        changing_components[i].value = result.x[i]

    optimal_netlist = netlist    
    for changed_component in changing_components:
        for netlist_component in optimal_netlist.components:
            if changed_component.name == netlist_component.name:
                netlist_component.value = changed_component.value
                netlist_component.modified = True
                break

    # TODO: Write out optimal_netlist object to file (relies on Aidan)
    optimal_netlist.class_to_file(local_netlist_file)

# TEMPORARY TESTING VALUES
ORIG_NETLIST_PATH = r"C:\Users\User\capstone\csce483CapstoneSpring2025\netlist.txt"
WRITABLE_NETLIST_PATH = r"C:\Users\User\capstone\csce483CapstoneSpring2025\netlistCopy.txt"

# TODO: 4 Volts bad, 3 Volts good
TARGET_VALUE = 'V(2)'
TEST_FIELDS = ['TIME', 'V(2)']
TEST_ROWS = [[0.00000000e+00, 4.00000000e+00],
        [4.00000000e-04, 4.00000000e+00],
        [8.00000000e-04, 4.00000000e+00],
        [1.20000000e-03, 4.00000000e+00],
        [1.60000000e-03, 4.00000000e+00],
        [2.00000000e-03, 4.00000000e+00]]

TEST_NETLIST = Netlist(ORIG_NETLIST_PATH)
# MAKE VALUES NOT DUMB IN A DUMB DUMB TEMP WAY
for component in TEST_NETLIST.components:
    if component.value == "1K":
        component.value = 1000
    elif component.value == "0.47u":
        component.value = 0.47e-6
    else:
        component.value = float(component.value)
    component.variable = True


# END TEMPORARY TESTING VALUES

# TEMPORARY
curvefit_optimize(TEST_FIELDS, TEST_ROWS, TEST_NETLIST)
# END TEMPORARY