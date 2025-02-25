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


myNetlist = Netlist("buck.txt")

# print("Values pre class to file:")
# print(myNetlist.components[2].name)
# print(myNetlist.components[2].type)
# print(myNetlist.components[2].value)
# print(myNetlist.components[2].variable)
# print(myNetlist.components[2].modified)

# print(myNetlist.components[3].name)
# print(myNetlist.components[3].type)
# print(myNetlist.components[3].value)
# print(myNetlist.components[3].variable)
# print(myNetlist.components[3].modified)


# myNetlist.components[2].modified = True
# myNetlist.components[2].value = "2021"
# myNetlist.components[3].modified = True
# myNetlist.components[3].value = "2025"
# myNetlist.class_to_file("buck.txt")

# print("Values post class to file:")
# print(myNetlist.components[2].name)
# print(myNetlist.components[2].type)
# print(myNetlist.components[2].value)
# print(myNetlist.components[2].variable)
# print(myNetlist.components[2].modified)

# print(myNetlist.components[3].name)
# print(myNetlist.components[3].type)
# print(myNetlist.components[3].value)
# print(myNetlist.components[3].variable)
# print(myNetlist.components[3].modified)