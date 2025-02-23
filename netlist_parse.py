#print("Test message for netlist parse")
#print("Second Message")
#print("Third Message")
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
            #print(f.read())
            #------Parsing Logic------#
            #Current Behavior: Skip Title Line, Commands, and non RLC components
                file.readline()
                for line in file:
                    values=line.strip().split(" ")
                    if(values == [""]):
                        continue
                    if(values[0][0] != "R" and values[0][0] != "L" and values[0][0] != "C"):
                        continue
                    #TODO: Need to deal with component value conversions
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

myNetlist = Netlist("buck.txt")

print(myNetlist.components[0].name)
print(myNetlist.components[0].type)
print(myNetlist.components[0].value)
print(myNetlist.components[0].variable)
print(myNetlist.components[0].modified)

print(myNetlist.components[1].name)
print(myNetlist.components[1].type)
print(myNetlist.components[1].value)
print(myNetlist.components[1].variable)
print(myNetlist.components[1].modified)
        