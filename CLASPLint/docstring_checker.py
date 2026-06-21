"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.docstring_checker — Validates that functions, methods, and classes have proper docstrings per CLASP 3.0.

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
import re
from typing import List, Optional, Set

from .reporter import Violation

# Define the set of parameter names exempt from docstring directive requirements.
parameters_exemptfromdocstring: Set[str] = {"self", "cls"}


class DocstringChecker(ast.NodeVisitor):
    """
    Walks the AST and validates docstring presence and Sphinx format for functions, methods, and classes.

    Public methods:
        visit_ClassDef — Checks that a class definition has a docstring present.
        visit_FunctionDef — Checks function and method docstrings and validates Sphinx :param/:type/:return format for methods.
        visit_AsyncFunctionDef — Delegates to visit_FunctionDef for async function docstring checking.

    Private methods:
        _init_source_line_function_ — Retrieves the source line text for a given AST node.
        _init_add_violation_function_ — Records a docstring-related violation with full source context.
        _init_check_format_function_ — Validates that a method docstring has matching Sphinx :param/:type/:return directives.
        _init_check_detail_function_ — Validates that the docstring includes a detailed description section between summary and directives.
        _init_scan_docstring_function_ — Parses a docstring and extracts Sphinx directive entries for comparison against the signature.
    """

    def __init__(self, string_filepath: str, list_sourcelines: List[str]):
        """
        Initialize the docstring checker with file path and source lines for context.

        Sets up the internal state needed to traverse the AST and report docstring violations.
        The source lines are stored for generating contextual violation messages with the
        original code line content.

        :param string_filepath: The absolute path to the Python file being checked.
        :type string_filepath: str
        :param list_sourcelines: The source code split into individual lines for context.
        :type list_sourcelines: list[str]
        """
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store source lines for contextual violation messages.
        self.list_sourcelines = list_sourcelines
        # Collect violations found during AST traversal.
        self.list_violations: List[Violation] = []
        # Track the current class name for contextual messages.
        self.string_currentclass: str = ""

    def _init_source_line_function_(self, node: ast.AST) -> str:
        """
        Retrieve the source line text for a given AST node.

        Uses the node's line number to index into the stored source lines list. Returns an
        empty string when the line number is unavailable or exceeds the source line count,
        ensuring safe access even for synthetic AST nodes.

        :param node: The AST node whose line number is used to look up the source line.
        :type node: ast.AST
        :return: The source line text at the node's line number, or an empty string.
        :rtype: str
        """
        # Return the source line if the node has a valid line number within bounds.
        if node.lineno and node.lineno <= len(self.list_sourcelines):
            # Retrieve and return the corresponding source line text.
            return self.list_sourcelines[node.lineno - 1]
        # Return an empty string if the line number is unavailable or out of range.
        return ""

    def _init_add_violation_function_(self, node: ast.AST, string_message: str) -> None:
        """
        Record a docstring-related violation with source context.

        Constructs a Violation data object with the file path, line number, docstring
        category tag, the provided message, and the source line for contextual display
        in violation reports.

        :param node: The AST node where the violation was detected, used for line number extraction.
        :type node: ast.AST
        :param string_message: The human-readable message describing the docstring violation.
        :type string_message: str
        """
        # Retrieve the source line associated with the violation node.
        string_sourceline = self._init_source_line_function_(node)
        # Append a new Violation to the violations list with full context.
        self.list_violations.append(Violation(
            # Supply the file path where the missing docstring was detected.
            string_filepath=self.string_filepath,
            # Supply the line number of the function or class definition.
            int_linenumber=node.lineno,
            # Supply the docstring violation category identifier.
            string_category="docstring",
            # Supply the human-readable missing-docstring message.
            string_message=string_message,
            # Supply the source line for contextual display.
            string_sourceline=string_sourceline,
        # Close the Violation data class instantiation.
        ))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Check the class for a docstring and then visit child nodes for methods.

        Classes only require a presence check; Sphinx format validation is not applied.

        :param node: The class definition AST node being visited.
        :type node: ast.ClassDef
        """
        # Classes only require presence check, not Sphinx format validation.
        if not ast.get_docstring(node):
            # Record a violation for the missing class docstring.
            self._init_add_violation_function_(
                # Pass the class definition node for line number extraction.
                node,
                # Build the message identifying the class missing a docstring.
                f"Class '{node.name}' is missing a docstring.",
            # Close the violation function call.
            )
        # Save the previous class context before entering the new class.
        string_previous = self.string_currentclass
        # Set the current class name for method context messages.
        self.string_currentclass = node.name
        # Visit child nodes within the class body to check methods.
        self.generic_visit(node)
        # Restore the previous class context after leaving the class.
        self.string_currentclass = string_previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Check the function or method for a docstring and validate Sphinx format for methods.

        Module-level functions only require a docstring to be present. Class methods additionally
        require Sphinx-style :param, :type, :return, and :rtype directives matching the signature.

        :param node: The function definition AST node being visited.
        :type node: ast.FunctionDef
        """
        # Retrieve the docstring text, or None if absent.
        string_docstring = ast.get_docstring(node)
        # Determine whether this is a method inside a class.
        bool_ismethod = bool(self.string_currentclass)
        # Determine the display name for violation messages.
        if bool_ismethod:
            # Build the qualified method name for display.
            string_displayname = f"Method '{self.string_currentclass}.{node.name}'"
        # Handle module-level functions that are not inside a class.
        else:
            # Build the function name for display.
            string_displayname = f"Function '{node.name}'"
        # Check that a docstring is present for this function or method.
        if not string_docstring:
            # Record a violation for the missing docstring.
            self._init_add_violation_function_(
                # Pass the function definition node.
                node,
                # Build the missing-docstring violation message.
                f"{string_displayname} is missing a docstring.",
            # Close the violation function call.
            )
            # Skip further format checks since there is no docstring to validate.
            self.generic_visit(node)
            # Exit early for functions without docstrings.
            return
        # Perform Sphinx format validation only for class methods.
        if bool_ismethod:
            # Validate the method docstring against the Sphinx directive format.
            self._init_check_format_function_(node, string_docstring, string_displayname)
        # Continue visiting the function body for nested definitions.
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """
        Check async function names using the same logic as regular functions.

        Delegates completely to visit_FunctionDef since async functions follow the same
        CLASP naming conventions and docstring requirements as their synchronous counterparts.

        :param node: The async function definition AST node being visited.
        :type node: ast.AsyncFunctionDef
        """
        # Delegate to the standard function definition visitor.
        self.visit_FunctionDef(node)

    def _init_check_format_function_(
            # Accept the function definition node for signature analysis.
            self, node: ast.FunctionDef,
            # Accept the raw docstring text for directive parsing.
            string_docstring: str,
            # Accept the pre-formatted display name for violation messages.
            string_displayname: str
    # Close the method parameter list without a return annotation requirement.
    ) -> None:
        """
        Validate that a method docstring follows Sphinx :param/:type/:return/:rtype format.

        Parses the docstring for Sphinx directives and compares them against the actual
        method signature parameters and return type annotation.

        :param node: The function definition AST node containing the method signature.
        :type node: ast.FunctionDef
        :param string_docstring: The docstring text extracted from the function node.
        :type string_docstring: str
        :param string_displayname: The human-readable method name for violation messages.
        :type string_displayname: str
        """
        # Check that the docstring includes a detailed description section.
        self._init_check_detail_function_(node, string_docstring, string_displayname)
        # Parse the docstring to extract Sphinx directive entries.
        dict_paramdescriptions, dict_paramtypes, set_returnentries = (
            # Delegate to the directive parsing helper method.
            self._init_scan_docstring_function_(string_docstring)
        # Unpack the returned directive collections.
        )
        # Collect the parameter names from the function signature excluding self and cls.
        list_parameters = [
            # Extract the argument name from each parameter node.
            arg.arg for arg in node.args.args
            # Exclude self and cls from docstring directive requirements.
            if arg.arg not in parameters_exemptfromdocstring
        # Close the list comprehension for parameter collection.
        ]
        # Include *args variadic parameter name if present.
        if node.args.vararg:
            # Add the variadic args name for directive checking.
            list_parameters.append(node.args.vararg.arg)
        # Include **kwargs variadic parameter name if present.
        if node.args.kwarg:
            # Add the variadic kwargs name for directive checking.
            list_parameters.append(node.args.kwarg.arg)
        # Check each normal parameter for :param and :type directives.
        for string_parameter in list_parameters:
            # Verify the :param directive exists for this parameter.
            if string_parameter not in dict_paramdescriptions:
                # Record a violation for missing :param directive.
                self._init_add_violation_function_(
                    # Pass the function definition node.
                    node,
                    # Build the message identifying the missing :param entry.
                    f"{string_displayname} docstring is missing "
                    # Append the parameter name to the :param directive message.
                    f"':param {string_parameter}:' directive.",
                # Close the violation function call.
                )
            # Verify the :type directive exists for this parameter.
            if string_parameter not in dict_paramtypes:
                # Record a violation for missing :type directive.
                self._init_add_violation_function_(
                    # Pass the function definition node.
                    node,
                    # Build the message identifying the missing :type entry.
                    f"{string_displayname} docstring is missing "
                    # Append the parameter name to the :type directive message.
                    f"':type {string_parameter}:' directive.",
                # Close the violation function call.
                )
        # Check for extra :param directives not in the actual parameter list.
        for string_extra in dict_paramdescriptions.keys() - set(list_parameters):
            # Record a violation for an extra :param directive.
            self._init_add_violation_function_(
                # Pass the function definition node.
                node,
                # Build the message identifying the unexpected :param entry.
                f"{string_displayname} docstring has unexpected "
                # Append the extra parameter name to the unexpected :param message.
                f"':param {string_extra}:' not in the method signature.",
            # Close the violation function call.
            )
        # Determine whether the method has a non-None return type annotation.
        bool_hasreturn = (
            # Check that a return annotation exists on the node.
            node.returns is not None
            # Only require :return if the type is not None.
            and not (isinstance(node.returns, ast.Constant) and node.returns.value is None)
        # Close the return-type-checking boolean expression.
        )
        # Check for :return directive when the method returns a value.
        if bool_hasreturn and not set_returnentries:
            # Record a violation for missing :return directive.
            self._init_add_violation_function_(
                # Pass the function definition node.
                node,
                # Build the message identifying the missing :return entry.
                f"{string_displayname} docstring is missing ':return:' directive "
                # Complete the message explaining the requirement.
                f"for its return type annotation.",
            # Close the violation function call.
            )

    def _init_check_detail_function_(
            # Accept the function definition node for violation reporting.
            self, node: ast.FunctionDef,
            # Accept the docstring text to analyze for section structure.
            string_docstring: str,
            # Accept the display name for violation messages.
            string_displayname: str
    # Close the method signature with no return annotation.
    ) -> None:
        """
        Check that the method docstring has a detailed description between summary and directives.

        The docstring must follow the format: brief summary line, blank line, detailed description
        paragraph(s), blank line, then :param/:type/:return directives.

        This validation ensures each method's docstring explains the specific logic and behavior
        of the implementation, not just the parameter and return value descriptions.

        :param node: The function definition AST node.
        :type node: ast.FunctionDef
        :param string_docstring: The docstring text to validate.
        :type string_docstring: str
        :param string_displayname: The human-readable method name for violation messages.
        :type string_displayname: str
        """
        # Split the docstring into individual lines for section analysis.
        list_lines = string_docstring.splitlines()
        # A valid multi-section docstring needs at least 3 lines: summary, blank, and one detail line.
        if len(list_lines) < 3:
            # Record a violation for docstrings that are too short to have a detail section.
            self._init_add_violation_function_(
                # Pass the function definition node.
                node,
                # Build the message about the missing detailed description.
                f"{string_displayname} docstring is missing a detailed "
                # Complete the message with the section description requirement.
                f"description section between the summary and directives.",
            # Close the violation function call.
            )
            # Exit early since the docstring is too short to analyze further.
            return
        # Skip the first line (summary) and the blank line after it.
        int_index = 2
        # Track whether any detailed description content was found.
        bool_hasdetail = False
        # Scan lines until reaching the directives section or end of docstring.
        while int_index < len(list_lines):
            # Get the current line with leading and trailing whitespace removed.
            string_line = list_lines[int_index].strip()
            # Detect the start of the directives section by matching :param or :return pattern.
            if string_line.startswith(":param") or string_line.startswith(":return") or string_line.startswith(":type") or string_line.startswith(":rtype"):
                # Stop scanning once directives begin.
                break
            # A non-blank, non-directive line counts as detailed description content.
            if string_line and not string_line.startswith(":param") and not string_line.startswith(":return") and not string_line.startswith(":type") and not string_line.startswith(":rtype"):
                # Mark that detailed description content was found.
                bool_hasdetail = True
            # Advance to the next line in the docstring.
            int_index += 1
        # Report a violation if no detailed description was found before the directives.
        if not bool_hasdetail:
            # Record a violation for the missing detailed description.
            self._init_add_violation_function_(
                # Pass the function definition node.
                node,
                # Build the message about the missing detailed description.
                f"{string_displayname} docstring is missing a detailed "
                # Complete the message with the section description requirement.
                f"description section between the summary and directives.",
            # Close the violation function call.
            )

    def _init_scan_docstring_function_(self, string_docstring: str):
        """
        Parse a docstring and extract :param, :type, and :return directive entries.

        Scans each line of the docstring for Sphinx-style directives and collects them
        into separate dictionaries for parameter descriptions, parameter types, and
        return declarations.

        :param string_docstring: The docstring text to parse for Sphinx directives.
        :type string_docstring: str
        :return: A tuple of (dict_paramdescriptions, dict_paramtypes, set_returnentries).
        :rtype: tuple[dict, dict, set]
        """
        # Initialize a dictionary for :param NAME: Description entries.
        dict_paramdescriptions: dict = {}
        # Initialize a dictionary for :type NAME: Type or :rtype NAME: Type entries.
        dict_paramtypes: dict = {}
        # Initialize a set to track whether :return directives are present.
        set_returnentries: set = set()
        # Split the docstring into individual lines for directive parsing.
        list_lines = string_docstring.splitlines()
        # Iterate over each line to detect Sphinx directives.
        for string_line in list_lines:
            # Strip leading and trailing whitespace from the current line.
            string_stripped = string_line.strip()
            # Match :param NAME: Description pattern.
            match_parameter = re.match(r'^:param\s+(\w+)\s*:', string_stripped)
            # Process :param directive when matched.
            if match_parameter:
                # Extract the parameter name from the :param directive.
                dict_paramdescriptions[match_parameter.group(1)] = True
                # Proceed to the next line after recording the :param entry.
                continue
            # Match :type NAME: Type or :rtype NAME: Type pattern.
            match_type = re.match(r'^:(?:type|rtype)\s+(\w+)\s*:', string_stripped)
            # Process :type or :rtype directive when matched.
            if match_type:
                # Extract the parameter or return name from the :type/:rtype directive.
                dict_paramtypes[match_type.group(1)] = True
                # Proceed to the next line after recording the type entry.
                continue
            # Match :return or :returns directive (with or without a name).
            if re.match(r'^:(?:return|returns)\b', string_stripped):
                # Record the presence of a :return directive.
                set_returnentries.add(True)
                # Proceed to the next line after detecting the :return entry.
                continue
        # Return the parsed directive collections as a tuple.
        return dict_paramdescriptions, dict_paramtypes, set_returnentries
