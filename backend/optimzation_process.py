
import time
import shutil

from backend.curvefit_optimization import curvefit_optimize

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
        #NODE CONSTRAINTS NOT IMPLENTED RN
        NODE_CONSTRAINTS = {}

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
        #self.add_part_constraints(curveData["constraints"], NETLIST)

        #Function call for writing proper commands to copy netlist here I think (Joseph's stuff)
        endValue = max([sublist[0] for sublist in TEST_ROWS])
        initValue = min([sublist[0] for sublist in TEST_ROWS])
        shutil.copyfile(NETLIST.file_path, WRITABLE_NETLIST_PATH)
        NETLIST.class_to_file(WRITABLE_NETLIST_PATH)
        NETLIST.writeTranCmdsToFile(WRITABLE_NETLIST_PATH,(endValue- initValue)/ 100,endValue,initValue,(endValue- initValue)/ 100,TARGET_VALUE)
        #Optimization Call
        optim = curvefit_optimize(TARGET_VALUE, TEST_ROWS, NETLIST, WRITABLE_NETLIST_PATH, NODE_CONSTRAINTS,queue)
        # print(type(optim))

        #Update AppData
        queue.put(("UpdateNetlist",NETLIST))
        queue.put(("UpdateOptimizationResults",optim))
        
        print(f"Optimization Results: {optim}")
        queue.put(("Update", f"Optimization Results: {optim}"))  
    except:
        queue.put(("Failed","Xyce failed"))