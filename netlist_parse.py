# Class Declaration
class Component:
    def __init__(self, name="", type="", value=0, variable=False, modified=False):
        self.name = name
        self.type = type
        self.value = value
        self.variable = variable
        self.modified = modified

class Netlist:
    def __init__(self, file_path):
        self.components = self.parse_file(file_path)
        self.file_path = file_path

    def parse_file(self, file_path) -> list:
    # Current Behavior: Parses file for RLC values to place into netlist's list. Skips Title Line, Commands, and non RLC components
        components = []
        try:
            with open(file_path,"r") as file:
            #Parsing Logic
                file.readline()
                for line in file:
                    values=line.strip().split(" ")
                    if(values == [""]):
                        continue
                    if(values[0][0] != "R" and values[0][0] != "L" and values[0][0] != "C"):
                        continue
##################### TODO: Need to deal with component value conversions possibly. Just floating right now, but doesn't help for 1K, 31u, etc.#####################
                    newComponent = Component(values[0],values[0][0],float(values[3]))
                    components.append(newComponent)
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return components
    
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
            for line in data:
                lineData = line.strip().split(" ")
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

# Test Statements
# myNetlist = Netlist("buck.txt")
# print("Values pre class to file:")
# print(myNetlist.components[2].name)
# print(myNetlist.components[2].type)
# print(myNetlist.components[2].value)
# print(myNetlist.components[2].variable)
# print(myNetlist.components[2].modified)

# print(type(myNetlist.components[2].name))
# print(type(myNetlist.components[2].type))
# print(type(myNetlist.components[2].value))
# print(type(myNetlist.components[2].variable))
# print(type(myNetlist.components[2].modified))

# print(myNetlist.components[3].name)
# print(myNetlist.components[3].type)
# print(myNetlist.components[3].value)
# print(myNetlist.components[3].variable)
# print(myNetlist.components[3].modified)


# myNetlist.components[2].modified = True
# myNetlist.components[2].value = 2021
# myNetlist.components[3].modified = True
# myNetlist.components[3].value = 2025
# myNetlist.class_to_file("buck.txt")

# print("Values post class to file:")
# print(myNetlist.components[2].name)
# print(myNetlist.components[2].type)
# print(myNetlist.components[2].value)
# print(myNetlist.components[2].variable)
# print(myNetlist.components[2].modified)

# print(type(myNetlist.components[2].name))
# print(type(myNetlist.components[2].type))
# print(type(myNetlist.components[2].value))
# print(type(myNetlist.components[2].variable))
# print(type(myNetlist.components[2].modified))

# print(myNetlist.components[3].name)
# print(myNetlist.components[3].type)
# print(myNetlist.components[3].value)
# print(myNetlist.components[3].variable)
# print(myNetlist.components[3].modified)