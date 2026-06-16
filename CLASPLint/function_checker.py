# Check function and class names against CLASP 3.0 naming conventions.

import ast
from typing import List

from .naming_utils import (
    validate_function_name,
    validate_class_name,
    length_namemax,
)
from .reporter import Violation


class FunctionChecker(ast.NodeVisitor):
    """Walk the AST and check function and class names against CLASP 3.0 rules."""

    def __init__(self, string_filepath: str, list_sourcelines: List[str]):
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store source lines for contextual violation messages.
        self.list_sourcelines = list_sourcelines
        # Collect violations found during AST traversal.
        self.list_violations: List[Violation] = []
        # Track the current class context for method detection.
        self.string_currentclass: str = ""

    def _init_source_line_function_(self, node: ast.AST) -> str:
        """Retrieve the source line text for a given AST node."""
        # Return the source line if the node has a valid line number within bounds.
        if node.lineno and node.lineno <= len(self.list_sourcelines):
            # Retrieve and return the corresponding source line text.
            return self.list_sourcelines[node.lineno - 1]
        # Return an empty string if the line number is unavailable or out of range.
        return ""

    def _init_add_violations_function_(self, string_name: str, string_category: str,
                         list_issues: list, node: ast.AST) -> None:
        """Record a list of naming violations with source context."""
        # Retrieve the source line associated with the violation node.
        string_sourceline = self._init_source_line_function_(node)
        # Append each issue as a Violation to the violations list.
        for string_message in list_issues:
            self.list_violations.append(Violation(
                string_filepath=self.string_filepath,
                int_linenumber=node.lineno,
                string_category=string_category,
                string_message=string_message,
                string_sourceline=string_sourceline,
            ))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check the class name for PascalCase format and abbreviation violations."""
        # Validate the class name against CLASP 3.0 class naming rules.
        list_issues = validate_class_name(node.name)
        # Record any class name violations found.
        self._init_add_violations_function_(node.name, "function", list_issues, node)
        # Save the previous class context before entering the new class.
        string_previous = self.string_currentclass
        # Set the current class context for method detection.
        self.string_currentclass = node.name
        # Visit child nodes within the class body.
        self.generic_visit(node)
        # Restore the previous class context after leaving the class.
        self.string_currentclass = string_previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check the function or method name for snake_case and abbreviation violations."""
        # Determine whether this function is a method inside a class.
        bool_ismethod = bool(self.string_currentclass)
        # Validate the function name against CLASP 3.0 function naming rules.
        list_issues = validate_function_name(node.name, is_method=bool_ismethod)
        # Use the "function" category for all function and method violations.
        string_category = "function"
        # Record any function name violations found.
        self._init_add_violations_function_(node.name, string_category, list_issues, node)
        # Check method name length for public methods specifically.
        if bool_ismethod and len(node.name) > length_namemax:
            # Record a violation for excessively long method names.
            self.list_violations.append(Violation(
                string_filepath=self.string_filepath,
                int_linenumber=node.lineno,
                string_category=string_category,
                string_message=(
                    f"Method '{node.name}' exceeds {length_namemax} characters "
                    f"(length: {len(node.name)})."
                ),
                string_sourceline=self._init_source_line_function_(node),
            ))
        # Continue visiting the function body for nested definitions.
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function names using the same logic as regular functions."""
        # Delegate to the standard function definition visitor.
        self.visit_FunctionDef(node)
