import re
from typing import List, Tuple, NamedTuple, Set, Union
from dataclasses import dataclass


class NetlistError(Exception):
    """Custom exception for netlist parsing and modification errors."""

    pass


@dataclass
class Component:
    """Represents a circuit component."""

    name: str
    type: str
    nodes: Tuple[str, ...]
    value: str  # Keep as string initially for flexibility.
    variable: bool = False


def parse_netlist(file_path: str) -> Tuple[List[Component], List[str]]:
    """Parses a netlist file. Returns components and a sorted list of unique nodes."""
    components = []
    nodes: Set[str] = set()  # Use a set for uniqueness, then convert to list
    try:
        with open(file_path, "r") as file:
            # Skip the first line (assuming it's a title/comment)
            next(file, None)  # Use next with a default to avoid StopIteration

            for line in file:
                line = line.strip()
                if not line or line.startswith("*"):  # Skip comments and empty lines
                    continue

                parts = line.split()
                if not parts:
                    continue  # Skip empty lines

                comp_type = parts[0][0].upper()
                name = parts[0]

                # Check for ;OPTIMIZE flag (case-insensitive)
                variable = False
                if ";" in line:
                    parts_semicolon = line.split(";")
                    for part in parts_semicolon:
                        if part.strip().upper() == "OPTIMIZE":
                            variable = True
                            break

                if comp_type in ("R", "L", "C"):
                    if len(parts) < 4:
                        raise NetlistError(f"Invalid RLC line: {line}")
                    nodes.update(parts[1:3])  # Add nodes to the set
                    try:
                        value = _component_value_conversion(
                            parts[3]
                        )  # Convert to float
                    except ValueError:
                        raise NetlistError(f"Invalid component value on line: {line}")
                    components.append(
                        Component(
                            name, comp_type, tuple(parts[1:3]), str(value), variable
                        )
                    )  # type: ignore

                elif comp_type in (
                    "B",
                    "D",
                    "F",
                    "H",
                    "I",
                    "V",
                    "W",
                ):  # Two-node components (and current sources)
                    if len(parts) < 3:
                        raise NetlistError(f"Invalid two-node component line: {line}")
                    nodes.update(parts[1:3])
                elif comp_type in ("J", "Q", "U", "Z"):  # Three-node
                    if len(parts) < 4:
                        raise NetlistError(f"Invalid three-node component line: {line}")
                    nodes.update(parts[1:4])
                elif comp_type in (
                    "E",
                    "G",
                    "M",
                    "O",
                    "S",
                    "T",
                    "X",
                    "K",
                    "A",
                ):  # Four or more- node
                    if len(parts) < 5:
                        raise NetlistError(f"Invalid component line: {line}")
                    nodes.update(parts[1:])  # Add all nodes
                # else:  # Removed the else, allow other components, but don't create objects

    except FileNotFoundError:
        raise NetlistError(f"Netlist file not found: {file_path}")
    except OSError as e:
        raise NetlistError(f"Error opening or reading netlist file: {e}")
    except NetlistError:
        raise  # Re-raise NetlistError
    except Exception as e:
        raise NetlistError(f"An unexpected error occurred during parsing: {e}")

    return components, sorted(list(nodes))  # Return sorted list of nodes


def update_netlist_file(netlist_path: str, components: List[Component]) -> None:
    """Updates the netlist file with modified component values."""
    try:
        with open(netlist_path, "r") as file:
            lines = file.readlines()

        updated_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("*") or line.startswith("."):
                updated_lines.append(line + "\n")  # Keep original formatting
                continue

            parts = line.split()
            if not parts:
                updated_lines.append(line + "\n")
                continue

            comp_name = parts[0]
            for comp in components:
                if comp.name == comp_name:
                    if comp.type in ("R", "L", "C"):
                        # Reconstruct the line with the updated value
                        new_line = (
                            f"{comp.name} {comp.nodes[0]} {comp.nodes[1]} {comp.value}"
                        )
                        if comp.variable:
                            new_line += " ;OPTIMIZE"  # Re add optimization flag
                        updated_lines.append(new_line + "\n")

                    break  # Important: Stop searching after finding the component
            else:  # No break occurred, component not found for this line
                updated_lines.append(line + "\n")  # Keep original line

        with open(netlist_path, "w") as file:
            file.writelines(updated_lines)

    except FileNotFoundError:
        raise NetlistError(f"Netlist file not found: {netlist_path}")
    except OSError as e:
        raise NetlistError(f"Error writing to netlist file: {e}")
    except Exception as e:
        raise NetlistError(f"An unexpected error occurred while updating: {e}")


def _component_value_conversion(str_val: str) -> Union[float, str]:
    """Converts component value strings (e.g., '1k', '0.47u') to floats."""
    data = {
        "Y": 24,
        "Z": 21,
        "E": 18,
        "P": 15,
        "T": 12,
        "G": 9,
        "M": 6,
        "k": 3,
        "K": 3,
        "": 0,
        "m": -3,
        "µ": -6,
        "u": -6,
        "n": -9,
        "p": -12,
        "f": -15,
        "a": -18,
        "z": -21,
        "y": -24,
    }
    str_val = str_val.strip()
    if not str_val:  # check for empty string
        raise ValueError("Empty component value string.")

    last_char = str_val[-1]
    if last_char.isdigit():  # No suffix
        return float(str_val)
    elif last_char in data:
        base_val = str_val[:-1]
        try:
            return float(base_val) * (10 ** data[last_char])
        except ValueError:
            raise ValueError(f"Invalid component value format: {str_val}")

    else:
        raise ValueError(f"Invalid component value suffix: {last_char}")


def netlist_to_string(components: List[Component]) -> str:
    """Convert a component list to a netlist string."""
    netlist_str = ""
    for comp in components:
        netlist_str += f"{comp.name} {comp.nodes[0]} {comp.nodes[1]} {comp.value}"
        if comp.variable:
            netlist_str += " ;OPTIMIZE"  # Add ;OPTIMIZE
        netlist_str += "\n"
    return netlist_str
