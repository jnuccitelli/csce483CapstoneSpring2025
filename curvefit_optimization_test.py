import subprocess
import scipy.optimize
import shutil

def curvefit_optimize(target_curve: list, netlist: Netlist) -> None:
    # Copy netlist file
    local_netlist_file = shutil.copyfile(ORIG_NETLIST_PATH, WRITABLE_NETLIST_PATH)
    # Parse target_curve to figure out what Y value is

    # Parse netlist to figure out which parts are subject to change
    # Divy out runs with parts changed and local Netlist objects-> Make a bunch of temporary netlist files with slight changes if we want simultaneous runs
    # Spawn Xyce process
    # See which Xyce output has lowest LSR using scipy and use associated Netlist object
    # Write out best Netlist object

# TEMPORARY TESTING VALUES
ORIG_NETLIST_PATH = r"C:\Users\User\capstone\csce483CapstoneSpring2025\netlist.txt"
WRITABLE_NETLIST_PATH = r"C:\Users\User\capstone\csce483CapstoneSpring2025\netlistCopy.txt"


curvefit_optimize()