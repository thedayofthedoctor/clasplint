# Check variable names against CLASP 3.0 group1_group2 format and abbreviation rules.

import ast
from typing import List

from .naming_utils import (
    validate_variable_name,
    length_namemax,
    names_exempt,
)
from .reporter import Violation


class VariableChecker(ast.NodeVisitor):
    """Walk the AST and check variable names against CLASP 3.0 rules."""

    def __init__(self, string_filepath: str, list_sourcelines: List[str]):
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store source lines for contextual violation messages.
        self.list_sourcelines = list_sourcelines
        # Collect violations found during AST traversal.
        self.list_violations: List[Violation] = []
        # Track checked assignments to avoid duplicate violation reports.
        self.set_checked: set = set()

    def _init_check_name_function_(self, string_name: str, node: ast.AST) -> None:
        """Validate a single variable name and record any violations."""
        # Skip dunder names as they follow Python's internal convention.
        if string_name.startswith("__") and string_name.endswith("__"):
            # Exit early for dunder names.
            return
        # Skip names in the exemption set (self, cls, _).
        if string_name in names_exempt:
            # Exit early for exempt variable names.
            return
        # Build a unique key to prevent duplicate checks for the same name and line.
        tuple_key = (string_name, node.lineno)
        # Skip if this name-and-line combination has already been checked.
        if tuple_key in self.set_checked:
            # Exit early for already-checked name and line combinations.
            return
        # Mark this name-and-line combination as checked.
        self.set_checked.add(tuple_key)
        # Run the CLASP 3.0 variable name validation.
        list_issues = validate_variable_name(string_name)
        # Retrieve the source line for contextual output.
        string_sourceline = ""
        # Ensure the line number is within bounds before accessing source lines.
        if node.lineno and node.lineno <= len(self.list_sourcelines):
            string_sourceline = self.list_sourcelines[node.lineno - 1]
        # Append each detected violation to the violations list.
        for string_message in list_issues:
            self.list_violations.append(Violation(
                string_filepath=self.string_filepath,
                int_linenumber=node.lineno,
                string_category="variable",
                string_message=string_message,
                string_sourceline=string_sourceline,
            ))

    def visit_Assign(self, node: ast.Assign) -> None:
        """Check variable names in assignment statements."""
        # Walk each assignment target to extract variable names.
        for target_node in node.targets:
            self._init_walk_target_function_(target_node)
        # Continue visiting child nodes for nested assignments.
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Check variable names in annotated assignment statements."""
        # Process the annotation target if present.
        if node.target:
            self._init_walk_target_function_(node.target)
        # Continue visiting child nodes.
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        """Check variable names introduced via the walrus operator :="."""
        # Walk the walrus operator target to extract the name.
        self._init_walk_target_function_(node.target)
        # Continue visiting child nodes.
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Check loop variable names in for statements."""
        # Walk the loop target to extract loop variable names.
        self._init_walk_target_function_(node.target)
        # Continue visiting child nodes including the loop body.
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function parameter names for CLASP 3.0 compliance."""
        # Check each positional parameter name.
        for node_argument in node.args.args:
            self._init_check_name_function_(node_argument.arg, node_argument)
        # Check each keyword-only parameter name.
        for kwnode_argument in node.args.kwonlyargs:
            self._init_check_name_function_(kwnode_argument.arg, kwnode_argument)
        # Check the *args variadic parameter name if present.
        if node.args.vararg:
            self._init_check_name_function_(node.args.vararg.arg, node.args.vararg)
        # Check the **kwargs variadic parameter name if present.
        if node.args.kwarg:
            self._init_check_name_function_(node.args.kwarg.arg, node.args.kwarg)
        # Continue visiting the function body for nested variable definitions.
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Check variable names bound in with-statement 'as' clauses."""
        # Iterate over each context manager item in the with statement.
        for item_node in node.items:
            # Process the optional variable binding if present.
            if item_node.optional_vars:
                self._init_walk_target_function_(item_node.optional_vars)
        # Continue visiting child nodes.
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Check exception variable names in except ... as clauses."""
        # Process the exception binding name if present.
        if node.name:
            self._init_check_name_function_(node.name, node)
        # Continue visiting child nodes in the handler body.
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        """Check variable names in global declarations."""
        # Validate each name declared as global.
        for string_name in node.names:
            self._init_check_name_function_(string_name, node)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        """Check variable names in nonlocal declarations."""
        # Validate each name declared as nonlocal.
        for string_name in node.names:
            self._init_check_name_function_(string_name, node)

    def _init_walk_target_function_(self, target: ast.AST) -> None:
        """Recursively walk assignment targets to extract variable names."""
        # Extract the identifier from a simple Name node.
        if isinstance(target, ast.Name):
            self._init_check_name_function_(target.id, target)
        # Recurse into tuple unpacking targets.
        elif isinstance(target, (ast.Tuple, ast.List)):
            # Iterate over each element in the unpacking target.
            for element_node in target.elts:
                self._init_walk_target_function_(element_node)
        # Unwrap starred expressions in unpacking.
        elif isinstance(target, ast.Starred):
            self._init_walk_target_function_(target.value)
        # Skip attribute assignments (obj.attr = ...) as these are not variable definitions.
        elif isinstance(target, ast.Attribute):
            # Take no action for attribute assignment targets.
            pass
        # Skip subscript assignments (obj[key] = ...) as these are not variable definitions.
        elif isinstance(target, ast.Subscript):
            # Take no action for subscript assignment targets.
            pass
