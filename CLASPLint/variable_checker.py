"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.variable_checker — AST visitor that validates variable names against CLASP 3.0 rules.

Author: Matt Belfast Brown
Create Date: 2026-06-17
Version Date: 2026-06-21
Version: 0.2.0

THIS PROGRAM IS LICENSED UNDER GPL-3.0
YOU SHOULD HAVE RECEIVED A COPY OF GPL-3.0 LICENSE.

Copyright (C) 2026 Matt Belfast Brown

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import ast
from typing import List

from .naming_utils import (
    # Import the main variable name validation function.
    validate_variable_name,
    # Import the maximum allowed name length constant.
    length_namemax,
    # Import the set of exempt variable names.
    names_exempt,
# Close the parenthesized import block.
)
from .reporter import Violation


class VariableChecker(ast.NodeVisitor):
    """
    AST node visitor that enforces CLASP 3.0 variable naming conventions.

    Public methods:
        visit_Assign — Validate variable names in plain assignment statements.
        visit_AnnAssign — Validate variable names in annotated assignment statements.
        visit_NamedExpr — Validate variable names introduced via the walrus operator.
        visit_For — Validate loop variable names in for-statement targets.
        visit_FunctionDef — Validate function parameter names for CLASP 3.0 compliance.
        visit_With — Validate variable names bound in with-statement clauses.
        visit_ExceptHandler — Validate exception variable names in except clauses.
        visit_Global — Validate variable names declared in global statements.
        visit_Nonlocal — Validate variable names declared in nonlocal statements.

    Private methods:
        _init_check_name_function_ — Validate a single name and record any violations.
        _init_walk_target_function_ — Recursively walk assignment targets to extract names.
    """

    def __init__(self, string_filepath: str, list_sourcelines: List[str]):
        """
        Initialize the variable checker with file path and source lines for context.

        Stores the file path and source lines for use during AST traversal and violation
        reporting. Initializes the violations list and a deduplication set to prevent
        reporting the same variable name twice on the same line.

        :param string_filepath: Absolute or relative path to the source file being checked.
        :type string_filepath: str
        :param list_sourcelines: Source code lines of the file for contextual violation messages.
        :type list_sourcelines: List[str]
        """
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store source lines for contextual violation messages.
        self.list_sourcelines = list_sourcelines
        # Collect violations found during AST traversal.
        self.list_violations: List[Violation] = []
        # Track checked assignments to avoid duplicate violation reports.
        self.set_checked: set = set()

    def _init_check_name_function_(self, string_name: str, node: ast.AST) -> None:
        """
        Validate a single variable name against CLASP 3.0 rules and record any violations.

        Skips dunder names, exempt names, and previously checked name-and-line combinations
        before delegating to the validation utility. Each detected issue is collected as a
        Violation with full file and line context.

        :param string_name: The variable name string to validate.
        :type string_name: str
        :param node: The AST node from which the variable name originates.
        :type node: ast.AST
        """
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
            # Retrieve the source line at the detected line number.
            string_sourceline = self.list_sourcelines[node.lineno - 1]
        # Append each detected violation to the violations list.
        for string_message in list_issues:
            # Construct a Violation with full file and line context.
            self.list_violations.append(Violation(
                # Supply the file path where the violation was detected.
                string_filepath=self.string_filepath,
                # Supply the line number of the offending variable name.
                int_linenumber=node.lineno,
                # Supply the violation category identifier.
                string_category="variable",
                # Supply the human-readable violation message.
                string_message=string_message,
                # Supply the source line for contextual display.
                string_sourceline=string_sourceline,
            # Close the Violation data class instantiation.
            ))

    def visit_Assign(self, node: ast.Assign) -> None:
        """
        Check variable names in assignment statements for CLASP 3.0 compliance.

        Iterates over all assignment targets in the statement, recursively walking each
        one to extract variable names for validation. The visitor continues into child
        nodes after processing targets.

        :param node: The assignment AST node whose targets contain variable names.
        :type node: ast.Assign
        """
        # Walk each assignment target to extract variable names.
        for target_node in node.targets:
            # Recursively walk the assignment target to validate names.
            self._init_walk_target_function_(target_node)
        # Continue visiting child nodes for nested assignments.
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """
        Check variable names in annotated assignment statements for CLASP 3.0 compliance.

        Processes the annotated assignment target if present, recursively extracting and
        validating variable names. The visitor continues traversing child nodes after
        the target check.

        :param node: The annotated assignment AST node whose target contains a variable name.
        :type node: ast.AnnAssign
        """
        # Process the annotation target if present.
        if node.target:
            # Recursively walk the annotated assignment target.
            self._init_walk_target_function_(node.target)
        # Continue visiting child nodes.
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        """
        Check variable names introduced via the walrus operator := for CLASP 3.0 compliance.

        Extracts the variable name from the walrus operator's target and validates it
        against CLASP 3.0 rules. Traversal continues into child expressions after name
        checking.

        :param node: The named expression AST node whose target is a variable name.
        :type node: ast.NamedExpr
        """
        # Walk the walrus operator target to extract the name.
        self._init_walk_target_function_(node.target)
        # Continue visiting child nodes.
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """
        Check loop variable names in for-statement targets for CLASP 3.0 compliance.

        Extracts loop variable names from the for-loop target, handling both simple names
        and unpacking patterns. The visitor continues into the loop body and else clause
        after processing.

        :param node: The for-loop AST node whose target contains loop variable names.
        :type node: ast.For
        """
        # Walk the loop target to extract loop variable names.
        self._init_walk_target_function_(node.target)
        # Continue visiting child nodes including the loop body.
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Check function parameter names for CLASP 3.0 compliance.

        Checks all parameter categories including positional arguments, keyword-only
        arguments, *args, and **kwargs for CLASP 3.0 compliance. The visitor continues
        into the function body after parameter validation.

        :param node: The function definition AST node whose arguments contain parameter names.
        :type node: ast.FunctionDef
        """
        # Check each positional parameter name.
        for node_argument in node.args.args:
            # Validate the positional parameter name against CLASP 3.0 rules.
            self._init_check_name_function_(node_argument.arg, node_argument)
        # Check each keyword-only parameter name.
        for kwnode_argument in node.args.kwonlyargs:
            # Validate the keyword-only parameter name.
            self._init_check_name_function_(kwnode_argument.arg, kwnode_argument)
        # Check the *args variadic parameter name if present.
        if node.args.vararg:
            # Validate the variadic positional parameter name.
            self._init_check_name_function_(node.args.vararg.arg, node.args.vararg)
        # Check the **kwargs variadic parameter name if present.
        if node.args.kwarg:
            # Validate the variadic keyword parameter name.
            self._init_check_name_function_(node.args.kwarg.arg, node.args.kwarg)
        # Continue visiting the function body for nested variable definitions.
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """
        Check variable names bound in with-statement 'as' clauses for CLASP 3.0 compliance.

        Iterates over each context manager item and processes any optional variable bindings
        found in 'as' clauses. Recursive walking handles nested unpacking within
        with-statement targets.

        :param node: The with-statement AST node whose items contain optional variable bindings.
        :type node: ast.With
        """
        # Iterate over each context manager item in the with statement.
        for item_node in node.items:
            # Process the optional variable binding if present.
            if item_node.optional_vars:
                # Recursively walk the with-statement binding target.
                self._init_walk_target_function_(item_node.optional_vars)
        # Continue visiting child nodes.
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """
        Check exception variable names in except ... as clauses for CLASP 3.0 compliance.

        Validates the exception variable name bound via the 'as' clause in except handlers.
        The visitor continues into the handler body after the name check.

        :param node: The exception handler AST node whose name attribute is the bound variable.
        :type node: ast.ExceptHandler
        """
        # Process the exception binding name if present.
        if node.name:
            # Validate the exception binding variable name.
            self._init_check_name_function_(node.name, node)
        # Continue visiting child nodes in the handler body.
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        """
        Check variable names in global declarations for CLASP 3.0 compliance.

        Iterates over each name declared in the global statement and validates it against
        CLASP 3.0 naming rules. No child traversal is performed since global declarations
        contain no nested nodes.

        :param node: The global declaration AST node whose names list contains variable names.
        :type node: ast.Global
        """
        # Validate each name declared as global.
        for string_name in node.names:
            # Check the global variable name against CLASP 3.0 rules.
            self._init_check_name_function_(string_name, node)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        """
        Check variable names in nonlocal declarations for CLASP 3.0 compliance.

        Iterates over each name declared in the nonlocal statement and validates it against
        CLASP 3.0 naming rules. No child traversal is performed since nonlocal declarations
        contain no nested nodes.

        :param node: The nonlocal declaration AST node whose names list contains variable names.
        :type node: ast.Nonlocal
        """
        # Validate each name declared as nonlocal.
        for string_name in node.names:
            # Check the nonlocal variable name against CLASP 3.0 rules.
            self._init_check_name_function_(string_name, node)

    def _init_walk_target_function_(self, target: ast.AST) -> None:
        """
        Recursively walk assignment targets to extract variable names for validation.

        Recursively descends into assignment targets, handling Name nodes for direct
        validation, Tuple/List nodes for unpacking, Starred nodes for starred expressions,
        and skipping Attribute/Subscript nodes. Leaf Name nodes are validated via the
        name-checking method.

        :param target: The AST node representing an assignment target to walk recursively.
        :type target: ast.AST
        """
        # Extract the identifier from a simple Name node.
        if isinstance(target, ast.Name):
            # Delegate to the name-checking function for Name nodes.
            self._init_check_name_function_(target.id, target)
        # Recurse into tuple unpacking targets.
        elif isinstance(target, (ast.Tuple, ast.List)):
            # Iterate over each element in the unpacking target.
            for element_node in target.elts:
                # Recursively walk each element of the unpacking target.
                self._init_walk_target_function_(element_node)
        # Unwrap starred expressions in unpacking.
        elif isinstance(target, ast.Starred):
            # Recursively walk the value inside the starred expression.
            self._init_walk_target_function_(target.value)
        # Skip attribute assignments (obj.attr = ...) as these are not variable definitions.
        elif isinstance(target, ast.Attribute):
            # Take no action for attribute assignment targets.
            pass
        # Skip subscript assignments (obj[key] = ...) as these are not variable definitions.
        elif isinstance(target, ast.Subscript):
            # Take no action for subscript assignment targets.
            pass
