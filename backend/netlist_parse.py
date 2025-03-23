import numpy as np

# Class Declaration
class Component:
    def __init__(self, name="", type="", value=0, variable=False, modified=False, minVal = 0, maxVal = np.inf):
        self.name = name
        self.type = type
        self.value = value
        self.variable = variable
        self.modified = modified
        self.minVal = minVal
        self.maxVal = maxVal

class Netlist:
    def __init__(self, file_path):
        self.components, self.nodes = self.parse_file(file_path)
        self.file_path = file_path

    def parse_file(self, file_path) -> list:
    # Current Behavior: Parses file for RLC values to place into netlist's list. Skips Title Line, Commands, and non RLC components
        components = []
        nodes = set()
        try:
            with open(file_path,"r") as file:
            #Parsing Logic
                file.readline()
                subCkt = False
                for line in file:
                    values=line.strip().split()
                    #print(values)
                    if(values == [""] or not values):
                        continue
                    elif(values[0].upper() == ".SUBCKT"):
                        subCkt = True
                    elif(values[0].upper() == ".ENDS"):
                        subCkt = False
                    if(subCkt):
                        continue
                    match values[0][0].upper():
                        #Prob skipping K, X, @, not anymore aiden....
                        case 'X':
                            for i in range(1,len(values) - 1):
                                nodes.add(values[i])
                        case "A":
                            nodes.add(values[1])
                            nodes.add(values[2])
                            nodes.add(values[3])
                            nodes.add(values[4])
                            nodes.add(values[5])
                            nodes.add(values[6])
                            nodes.add(values[7])
                            nodes.add(values[8])
                        #Case for two node components
                        case "B" | "C" | "D" | "F" | "H" | "I" | "L" | "R" | "V" | "W":
##################### TODO: Need to deal with component value conversions possibly. Just floating right now, but doesn't help for 1K, 31u, etc.#####################
                            if values[0][0] == "R" or values[0][0] == "L" or values[0][0] == "C":
                                newComponent = Component(values[0],values[0][0], self.componentValConversion(values[3]))
                                components.append(newComponent)
                            nodes.add(values[1])
                            nodes.add(values[2])
                        #Case for three node components
                        case"J" | "Q" | "U" | "Z":
                            nodes.add(values[1])
                            nodes.add(values[2])
                            nodes.add(values[3])
                        #Case for four node components
                        case"E" | "G" |"M" | "O" | "S" | "T":
                            nodes.add(values[1])
                            nodes.add(values[2])
                            nodes.add(values[3])
                            nodes.add(values[4])
                        case _:
                            continue

        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return [components,nodes]
    
    def class_to_file(self, file_path):
    # Current Behavior: Reads in specified file and updates lines matching lines in the netlist class that have been marked as modified with the new value.
        try:
            # Get Current file netlist and modified components in class
            with open(file_path,"r") as file:
                data = file.readlines()
            modifiedComponents = []
            for component in self.components:
                if component.modified == True:
                    modifiedComponents.append(component)
                    component.modified = False
            # Generate updated netlist
            updatedData=[]
            ctrl = False
            for line in data:
                lineData = line.strip().split()
                if(not lineData):
                    continue
                #ignore lines in the unsuppotred .CONTROL directive
                if(lineData[0].upper() == ".CONTROL"):
                    crtl = True
                if(lineData[0].upper() == ".ENDC"):
                    crtl = False
                if(crtl):
                    continue
                
                for component in modifiedComponents:
                    if lineData[0] == component.name:
                        lineData[3] = component.value
                        line = f"{lineData[0]} {lineData[1]} {lineData[2]} {float(lineData[3])}\n"
                        modifiedComponents.remove(component)
                        break
                updatedData.append(line)
            with open(file_path,"w") as file:
                file.writelines(updatedData)
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def componentValConversion(self, strVal):
        data = {
        'Y': 24,
        'Z': 21,
        'E': 18,
        'P': 15,
        'T': 12,
        'G': 9,
        'M': 6,
        'k': 3,
        'K': 3,
        '': 0,
        'm': -3,
        'µ': -6,
        'u': -6,
        'n': -9,
        'p': -12,
        'f': -15,
        'a': -18,
        'z': -21,
        'y': -24
        }
        #print("The last value is: ")
        #print(strVal[-1])
        if strVal[-1] in data:
            baseVal = strVal[:-1]
            newStr= f"{baseVal}e{data[strVal[-1]]}"
            return float(newStr)
        else:
            return float(strVal)
# Test Statements
# myNetlist = Netlist("netlist.txt")
# print("Values pre class to file:")
# print(myNetlist.components[0].name)
# print(myNetlist.components[0].type)
# print(myNetlist.components[0].value)
# print(myNetlist.components[0].variable)
# print(myNetlist.components[0].modified)

# print(type(myNetlist.components[0].name))
# print(type(myNetlist.components[0].type))
# print(type(myNetlist.components[0].value))
# print(type(myNetlist.components[0].variable))
# print(type(myNetlist.components[0].modified))

# print(myNetlist.components[1].name)
# print(myNetlist.components[1].type)
# print(myNetlist.components[1].value)
# print(myNetlist.components[1].variable)
# print(myNetlist.components[1].modified)


# myNetlist.components[0].modified = True
# myNetlist.components[0].value = 2021
# myNetlist.components[1].modified = True
# myNetlist.components[1].value = 2025
# myNetlist.class_to_file("netlist.txt")

# print("Values post class to file:")
# print(myNetlist.components[0].name)
# print(myNetlist.components[0].type)
# print(myNetlist.components[0].value)
# print(myNetlist.components[0].variable)
# print(myNetlist.components[0].modified)

# print(type(myNetlist.components[0].name))
# print(type(myNetlist.components[0].type))
# print(type(myNetlist.components[0].value))
# print(type(myNetlist.components[0].variable))
# print(type(myNetlist.components[0].modified))

# print(myNetlist.components[1].name)
# print(myNetlist.components[1].type)
# print(myNetlist.components[1].value)
# print(myNetlist.components[1].variable)
# print(myNetlist.components[1].modified)

# print(myNetlist.nodes)