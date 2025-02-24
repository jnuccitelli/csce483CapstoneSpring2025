import re
import subprocess
import os
from typing import List, Tuple, Dict


def run_xyce_and_parse_prn(
    netlist_path: str, output_prn_path: str = None
) -> Tuple[List[str], List[List[float]]]:
    """
    Runs Xyce on the given netlist and parses the transient analysis output
    from the generated .prn file.

    Args:
        netlist_path: Path to the Xyce netlist file.
        output_prn_path: Optional. Path to the .prn file. If None,
            it's assumed to be <netlist_path>.prn in the same directory
            as the netlist.

    Returns:
        A tuple: (list of variable names, list of data arrays).
        See `parse_xyce_prn_output` for details.

    Raises:
        FileNotFoundError: If the netlist file or .prn file does not exist.
        subprocess.CalledProcessError: If Xyce returns a non-zero exit code.
        ValueError: If the output format is invalid or cannot be parsed.
        TimeoutError: If Xyce execution takes too long
    """
    try:
        # Determine output .prn path if not provided
        if output_prn_path is None:
            output_prn_path = netlist_path + ".prn"  # Corrected .prn naming

        # Run Xyce and capture stdout and stderr (for error checking)
        result = subprocess.run(
            ["Xyce", netlist_path],
            capture_output=True,
            text=True,
            check=True,  # Raise exception on non-zero exit code
            timeout=60,  # Timeout
        )

        # Parse the .prn file
        return parse_xyce_prn_output(output_prn_path)

    except FileNotFoundError:
        raise FileNotFoundError(f"Netlist file not found: {netlist_path}")
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(
            e.returncode, e.cmd, output=e.output, stderr=e.stderr
        )
    except ValueError as e:
        raise ValueError(
            f"Error parsing Xyce output: {e}"
        )  # Removed raw output, as it's not relevant
    except subprocess.TimeoutExpired as e:
        raise subprocess.TimeoutExpired(
            e.cmd, e.timeout, output=e.output, stderr=e.stderr
        )
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")


def parse_xyce_prn_output(prn_filepath: str) -> Tuple[List[str], List[List[float]]]:
    """
    Parses a Xyce .prn file containing transient analysis results.

    Args:
        prn_filepath: Path to the Xyce .prn file.

    Returns:
        A tuple: (list of variable names, list of data arrays).
        The variable names are strings (e.g., ['time', 'V(1)', 'V(2)']).
        The data arrays are lists of floats, one list per variable.

    Raises:
        FileNotFoundError: If the .prn file does not exist.
        ValueError: If the .prn file format is invalid or cannot be parsed.
    """

    try:
        with open(prn_filepath, "r") as f:
            lines = f.read().strip().split("\n")
    except FileNotFoundError:
        raise FileNotFoundError(f".prn file not found: {prn_filepath}")
    except Exception as e:
        raise Exception(f"Error reading .prn file: {e}")

    # Find the header line (starts with "Index" or "time")
    header_line_index = -1
    for i, line in enumerate(lines):
        if line.lower().startswith("index") or line.lower().startswith("time"):
            header_line_index = i
            break

    if header_line_index == -1:
        raise ValueError("Could not find header line in Xyce .prn output.")

    # Extract variable names from the header line
    header_line = lines[header_line_index]
    variable_names = header_line.split()
    if variable_names[0].lower() == "index":
        variable_names = variable_names[1:]  # Remove "index" if present

    # Prepare data lists (one for each variable)
    data: List[List[float]] = [[] for _ in variable_names]

    # Parse the data lines
    for line in lines[header_line_index + 1 :]:
        line = line.strip()
        if not line:  # Skip empty lines
            continue

        # --- ADDED CHECK: Stop if we encounter a non-data line ---
        if not re.match(r"^[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line):
            break  # Stop parsing if the line doesn't start with a number

        parts = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)

        if len(parts) != len(variable_names) + 1 and len(parts) != len(variable_names):
            raise ValueError(f"Incorrect number of values on data line: {line}")

        if len(parts) == len(variable_names) + 1:
            parts = parts[1:]  # Remove index if present

        # Convert to floats and append to the correct data lists
        try:
            for i, value_str in enumerate(parts):
                data[i].append(float(value_str))
        except ValueError:
            raise ValueError(f"Invalid numerical value on data line: {line}")

    return variable_names, data


if __name__ == "__main__":
    # Example Usage:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    netlist_file = os.path.join(script_dir, "netlist.txt")

    try:
        variable_names, data = run_xyce_and_parse_prn(netlist_file)
        print("Variable Names:", variable_names)
        print("Data:")
        for i, var_name in enumerate(variable_names):
            print(f"  {var_name}: {data[i][:10]} ...")
    except FileNotFoundError as e:
        print(e)
    except subprocess.CalledProcessError as e:
        print(f"Xyce failed with error code {e.returncode}:\n{e.stderr}")
    except ValueError as e:
        print(f"Error parsing output: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
