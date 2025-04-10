
import shutil

from backend.curvefit_optimization import curvefit_optimize

def add_part_constraints(constraints, netlist):
    equalConstraints = []
    for constraint in constraints:
        #Parse out  components
        if constraint["type"] == "parameter":
            left = constraint["left"].strip()
            right = constraint["right"].strip()

            componentVals = {}
            for component in netlist.components:
                componentVals[component.name] = component.value
            for component in netlist.components:
                if left == component.name:
                    match constraint["operator"]:
                        case ">=":
                            component.minVal = eval(right, componentVals)
                            if component.value <= component.minVal:
                                component.value = component.minVal + 1
                                component.modified = True
                                # Not sure about what to set other bound to 
                                component.maxVal = component.minVal *10
                            print(f"{component.name} minVal set to {component.minVal}")
                        case "=":
                            component.value = eval(right, componentVals)
                            component.variable = False
                            component.modified = True
                            equalConstraints.append(constraint)
                            print(f"{component.name} set to {component.value}")
                        case "<=":
                            component.maxVal = eval(right, componentVals)
                            if component.value >= component.maxVal:
                                component.value = component.maxVal - 1
                                component.modified = True
                                # Not sure about what to set other bound to 
                                component.minVal = component.maxVal/10
                            print(f"{component.name} maxVal set to {component.maxVal}")
                    break
    return equalConstraints
    

def add_node_constraints(constraints):
    formattedNodeConstraints = {}
    nodes = {}
    for constraint in constraints:
        if constraint["type"] == "node":
            nodes[constraint["left"].strip()] = [None,None]
    for constraint in constraints:
        if constraint["type"] == "node":
            match constraint["operator"]:
                        case ">=":
                            nodes[constraint["left"].strip()][0] = float(constraint["right"].strip())
                        case "<=":
                            nodes[constraint["left"].strip()][1] = float(constraint["right"].strip())
    for node in nodes:
        formattedNodeConstraints[node] = (nodes[node][0],nodes[node][1])
        #left = constraint["left"].strip()
        #right = float(constraint["right"].strip())
        #formattedNodeConstraints[left] = (None,None)
    return formattedNodeConstraints

def optimizeProcess(queue,curveData,testRows,netlistPath,netlistObject,selectedParameters):
    try:
        print("GOT HERE")
        
        print(f"curveData = {curveData}")
        #Replace with self.controller.get_app_data("optimization_settings) stuff
        TARGET_VALUE = curveData["y_parameter"]
        TEST_ROWS = testRows
        ORIG_NETLIST_PATH = netlistPath
        NETLIST = netlistObject
        WRITABLE_NETLIST_PATH = ORIG_NETLIST_PATH[:-4]+"Copy.txt"
        #NODE CONSTRAINTS 
        NODE_CONSTRAINTS = add_node_constraints(curveData["constraints"]) 

        print(f"TARGET_VALUE = {TARGET_VALUE}")
        print(f"ORIG_NETLIST_PATH = {ORIG_NETLIST_PATH}")
        print(f"NETLIST.components = {NETLIST.components}")
        print(f"NETLIST.file_path = {NETLIST.file_path}")
        print(f"WRIITABLE_NETLIST_PATH = {WRITABLE_NETLIST_PATH}")

        #UPDATE NETLIST BASED ON OPTIMIZATION SETTINGS AND CONSTRAINTS
        for component in NETLIST.components:
            if component.name in selectedParameters:
                component.variable = True

        #ADD IN INITIAL CONSTRAINTS TO NETLIST CLASS VIA MINVAL MAXVAL

        EQUALITY_PART_CONSTRAINTS = add_part_constraints(curveData["constraints"], NETLIST)

        #Function call for writing proper commands to copy netlist here I think (Joseph's stuff)
        endValue = max([sublist[0] for sublist in TEST_ROWS])
        initValue = min([sublist[0] for sublist in TEST_ROWS])
        shutil.copyfile(NETLIST.file_path, WRITABLE_NETLIST_PATH)
        NETLIST.class_to_file(WRITABLE_NETLIST_PATH)
        CONSTRAINED_NODES = []
        for constraint in curveData["constraints"]:
            if constraint["type"] == "node":
                if constraint["left"].strip() != TARGET_VALUE:
                    CONSTRAINED_NODES.append(constraint["left"].strip())
        NETLIST.writeTranCmdsToFile(WRITABLE_NETLIST_PATH,(endValue- initValue)/ 100,endValue,initValue,(endValue- initValue)/ 100,TARGET_VALUE,CONSTRAINED_NODES)
        #Optimization Call
        optim = curvefit_optimize(TARGET_VALUE, TEST_ROWS, NETLIST, WRITABLE_NETLIST_PATH, NODE_CONSTRAINTS, EQUALITY_PART_CONSTRAINTS,queue)
        # print(type(optim))

        #Update AppData
        queue.put(("UpdateNetlist",NETLIST))
        queue.put(("UpdateOptimizationResults",optim))
        
        print(f"Optimization Results: {optim}")
        queue.put(("Update", f"Optimization Results: {optim}"))  
    except Exception as e:
        queue.put(("Failed",f"{e}"))