import ast
import math
import re
from typing import Dict, Any, List, Tuple


class ExpressionEvaluator:
    """
    Handles the safe evaluation of mathematical expressions with support for
    variable substitution.
    """

    _allowed_names: Dict[str, Any] = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "log": math.log,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
    }

    def __init__(self, allowed_variables: List[str] = None) -> None:
        if allowed_variables is None:
            self.allowed_variables = []
        else:
            self.allowed_variables = allowed_variables

    def evaluate(self, expression: str, variables: Dict[str, float]) -> float:
        """
        Safely evaluates a mathematical expression, substituting variables.

        Args:
            expression: The expression string.
            variables:  A dictionary mapping variable names to their values.

        Returns:
            The result of the expression.

        Raises:
            ValueError: If the expression is invalid or contains disallowed
                names.
        """
        # Check if the expression contains only allowed characters and names
        allowed_chars_pattern = r"^[a-zA-Z0-9+\-*/().\s]+$"
        if not re.match(allowed_chars_pattern, expression):
            raise ValueError("Invalid characters in expression.")
        # Validate the expression using AST parsing for security
        try:
            parsed_expression = ast.parse(expression, mode="eval")
            for node in ast.walk(parsed_expression):
                if isinstance(node, ast.Name):
                    if (
                        node.id not in self._allowed_names
                        and node.id not in self.allowed_variables
                    ):
                        raise ValueError(f"Invalid name in expression: {node.id}")
                elif isinstance(node, ast.Call):
                    if (
                        not isinstance(node.func, ast.Name)
                        or node.func.id not in self._allowed_names
                    ):
                        raise ValueError(
                            f"Invalid function call in expression: {node.func.id if isinstance(node.func, ast.Name) else 'Unknown'}"
                        )  # type: ignore
        except SyntaxError as e:
            raise ValueError(f"Syntax error in expression: {e}") from e
        # Create safe namespace
        safe_namespace = {
            **self._allowed_names,
            **{
                var: variables[var]
                for var in variables
                if var in self.allowed_variables
            },
        }
        # Evaluate
        try:
            compiled_expression = compile(parsed_expression, "<string>", "eval")
            result = eval(compiled_expression, safe_namespace)
            return float(result)
        except (TypeError, NameError, AttributeError) as e:
            raise ValueError(f"Evaluation error: {e}") from e
        except Exception as e:
            raise ValueError(f"Unexpected error in expression evaluation: {e}") from e

    def validate_expression(self, expression: str) -> Tuple[bool, List[str]]:
        """
        Validates a mathematical expression, checking for allowed characters,
        functions, and variables.

        Args:
            expression: The expression string to validate.

        Returns:
            A tuple: (is_valid, used_variables).
            - is_valid: True if the expression is valid, False otherwise.
            - used_variables: A list of variable names found in the expression.

        Raises:
            Nothing, return type used.
        """
        # Check for allowed characters
        allowed_chars_pattern = r"^[a-zA-Z0-9+\-*/().\s=><]+$"
        if not re.match(allowed_chars_pattern, expression):
            return False, []

        # Extract potential variable names
        potential_variables = re.findall(r"[a-zA-Z][a-zA-Z0-9]*", expression)
        used_variables = []

        # Validate using AST parsing
        try:
            parsed_expression = ast.parse(expression, mode="eval")
            for node in ast.walk(parsed_expression):
                if isinstance(node, ast.Name):
                    # Check if it's a valid variable or allowed function
                    if (
                        node.id not in self._allowed_names
                        and node.id not in self.allowed_variables
                    ):
                        return False, []  # Invalid variable name
                    if node.id in potential_variables:
                        used_variables.append(node.id)
                elif isinstance(node, ast.Call):
                    # Check if it's an allowed function
                    if (
                        not isinstance(node.func, ast.Name)
                        or node.func.id not in self._allowed_names
                    ):
                        return False, []  # Invalid function call
        except SyntaxError:
            return False, []  # Invalid syntax

        return True, used_variables
