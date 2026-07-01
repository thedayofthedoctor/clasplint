# -*- coding: utf-8 -*-
"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.function_checker -- Validates function and class names against CLASP 3.1.1 naming rules.

Author: Matt Belfast Brown
Create Date: 2026-06-17
Version Date: 2026-07-01
Version: 0.3.0

THIS PROGRAM IS LICENSED UNDER GPL-3.0
YOU SHOULD HAVE RECEIVED A COPY OF GPL-3.0 LICENSE.

Copyright (C) 2026 Matt Belfast Brown

CLASPLint is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

CLASPLint is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CLASPLint.  If not, see <https://www.gnu.org/licenses/>.
"""

import ast
from typing import List, Union

from .naming_utils import (
    # Import the function name validation utility.
    validate_function_name,
    # Import the class name validation utility.
    validate_class_name,
    # Import the default configuration class for naming constraints.
    CLASPDefaults,
    # Close the parenthesized import block.
)
from .reporter import Violation


class FunctionChecker(ast.NodeVisitor):
    """
    Walks the AST and validates function and class names against CLASP 3.1.1 naming conventions.

    Public methods:
        visit_ClassDef -- Validates class names per PascalCase, detecting NodeVisitor inheritance.
        visit_FunctionDef -- Validates function/method names against snake_case and length limits.
        visit_AsyncFunctionDef -- Delegates to visit_FunctionDef for async function name checking.

    Private methods:
        _init_source_line_function_ -- Retrieves the source line text for a given AST node.
        _init_add_violations_function_ -- Records naming violations with full source context.
        _init_detect_visitor_function_ -- Detects NodeVisitor subclasses for visit_* exemption.
    """

    def __init__(self, string_filepath: str, list_sourcelines: List[str]):
        """
        Initialize the function checker with file path and source lines for context.

        Stores the file path and source lines for later violation reporting, initializes
        an empty violations list, and sets the current class context and AST visitor
        detection flags to their default unset states.

        :param string_filepath: The absolute or relative path to the file being checked.
        :type string_filepath: str
        :param list_sourcelines: The list of source code lines read from the file.
        :type list_sourcelines: List[str]
        """
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store source lines for contextual violation messages.
        self.list_sourcelines = list_sourcelines
        # Collect violations found during AST traversal.
        self.list_violations: List[Violation] = []
        # Track the current class context for method detection.
        self.string_currentclass: str = ""
        # Track whether the current class inherits from ast.NodeVisitor.
        self.bool_isastvisitor: bool = False

    def _init_source_line_function_(self, node: ast.AST) -> str:
        """
        Retrieve the source line text for a given AST node.

        Uses the node's line number attribute to index into the stored source lines list.
        Returns an empty string when the line number is absent or exceeds the source range.

        :param node: The AST node whose source line is to be retrieved.
        :type node: ast.AST
        :return: The source line text as a string, or an empty string if unavailable.
        :rtype: str
        """
        # Return the source line if the node has a valid line number within bounds.
        int_lineno = getattr(node, 'lineno', 0)
        # Guard against AST nodes that lack a line number attribute.
        if int_lineno and int_lineno <= len(self.list_sourcelines):
            # Retrieve and return the corresponding source line text.
            return self.list_sourcelines[int_lineno - 1]
        # Return an empty string if the line number is unavailable or out of range.
        return ""

    def _init_add_violations_function_(
            # Accept the violation category for grouping in the report.
            self, string_category: str,
            # Accept the list of violation issue strings to record.
            list_issues: list, node: ast.AST
            # Complete the method signature with no return annotation.
            ) -> None:
        """
        Record a list of naming violations with source context.

        Retrieves the source line for the given AST node, then constructs and appends
        a Violation object for each issue string in the provided list, bundling the
        file path, line number, category, message, and source line together.

        :param string_category: The category identifier for the violation type.
        :type string_category: str
        :param list_issues: The list of human-readable violation message strings.
        :type list_issues: list
        :param node: The AST node associated with the violation.
        :type node: ast.AST
        """
        # Retrieve the source line associated with the violation node.
        string_sourceline = self._init_source_line_function_(node)
        # Append each issue as a Violation to the violations list.
        for string_message in list_issues:
            # Construct a Violation with full file, line, and message context.
            self.list_violations.append(
                # Instantiate a Violation data class for this naming issue.
                Violation(
                    # Supply the file path where the violation was detected.
                    string_filepath=self.string_filepath,
                    # Supply the line number of the offending name.
                    int_linenumber=getattr(node, 'lineno', 0),
                    # Supply the violation category identifier.
                    string_category=string_category,
                    # Supply the human-readable violation message.
                    string_message=string_message,
                    # Supply the source line for contextual display.
                    string_sourceline=string_sourceline,
                    # Close the Violation constructor call.
                )
            )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Check the class name for PascalCase format and abbreviation violations.

        Validates the class name against CLASP 3.1.1 rules, saves and restores the
        current class context around visiting child nodes, and detects whether the
        class inherits from ast.NodeVisitor to enable targeted visit_* exemptions.

        :param node: The ClassDef AST node representing the class definition.
        :type node: ast.ClassDef
        """
        # Validate the class name against CLASP 3.1.1 class naming rules.
        list_issues = validate_class_name(node.name)
        # Record any class name violations found.
        self._init_add_violations_function_("function", list_issues, node)
        # Save the previous class context before entering the new class.
        string_previous = self.string_currentclass
        # Save the previous visitor flag before entering the new class.
        bool_previousvisitor = self.bool_isastvisitor
        # Set the current class context for method detection.
        self.string_currentclass = node.name
        # Determine whether this class inherits from ast.NodeVisitor for visit_* exemption.
        self.bool_isastvisitor = self._init_detect_visitor_function_(node)
        # Visit child nodes within the class body.
        self.generic_visit(node)
        # Restore the previous class context after leaving the class.
        self.string_currentclass = string_previous
        # Restore the previous visitor flag after leaving the class.
        self.bool_isastvisitor = bool_previousvisitor

    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        """
        Check the function or method name for snake_case and abbreviation violations.

        Determines whether the definition is a module-level function or a class method,
        validates the name with the appropriate context flags, and additionally checks
        public method names against the maximum allowed length limit.

        :param node: The FunctionDef AST node representing the function definition.
        :type node: ast.FunctionDef
        """
        # Determine whether this function is a method inside a class.
        bool_ismethod = bool(self.string_currentclass)
        # Validate the function name against CLASP 3.1.1 function naming rules.
        list_issues = validate_function_name(
            # Pass the function name to validate.
            node.name,
            # Indicate whether this is a method or a module-level function.
            is_method=bool_ismethod,
            # Pass the AST visitor flag for targeted visit_* exemption.
            is_astvisitor=self.bool_isastvisitor,
            # Close the function call arguments.
        )
        # Use the "function" category for all function and method violations.
        string_category = "function"
        # Record any function name violations found.
        self._init_add_violations_function_(string_category, list_issues, node)
        # Check method name length for public methods specifically.
        if bool_ismethod and len(node.name) > CLASPDefaults.length_namemax:
            # Record a violation for excessively long method names.
            self.list_violations.append(
                # Instantiate a Violation data class for the length issue.
                Violation(
                    # Supply the file path where the method was defined.
                    string_filepath=self.string_filepath,
                    # Supply the line number of the method definition.
                    int_linenumber=node.lineno,
                    # Supply the function category identifier.
                    string_category=string_category,
                    # Build the violation message with current and maximum lengths.
                    string_message=(
                        # Format the method name and maximum allowed length.
                        f"Method '{node.name}' exceeds {CLASPDefaults.length_namemax} characters "
                        # Append the actual length of the method name.
                        f"(length: {len(node.name)})."
                        # Close the parenthesized message string.
                    ),
                    # Supply the source line for contextual display.
                    string_sourceline=self._init_source_line_function_(node),
                    # Close the Violation constructor call.
                )
            )
        # Continue visiting the function body for nested definitions.
        self.generic_visit(node)

    # Mark this method as static since it inspects base classes without instance state.
    @staticmethod
    def _init_detect_visitor_function_(node: ast.ClassDef) -> bool:
        """
        Determine whether the class definition inherits from ast.NodeVisitor.

        Inspects each base class of the given ClassDef node and checks whether any
        base matches the ast.NodeVisitor attribute chain. Returns True immediately
        upon finding a match, or False after exhausting all bases.

        :param node: The ClassDef AST node whose base classes are inspected.
        :type node: ast.ClassDef
        :return: True if any base class is ast.NodeVisitor, False otherwise.
        :rtype: bool
        """
        # Iterate over each base class in the class definition.
        for node_base in node.bases:
            # Check for direct ast.NodeVisitor base class reference.
            if isinstance(node_base, ast.Attribute):
                # Verify the attribute chain matches ast.NodeVisitor.
                if (
                        # Check that the value is an ast Name node.
                        isinstance(node_base.value, ast.Name)
                        # Match the module name ast.
                        and node_base.value.id == "ast"
                        # Match the class name NodeVisitor.
                        and node_base.attr == "NodeVisitor"
                        # Close the attribute-chain check.
                ):
                    # Confirm that the class inherits from ast.NodeVisitor.
                    return True
        # No ast.NodeVisitor base class was found in the inheritance chain.
        return False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """
        Check async function names using the same logic as regular functions.

        Delegates directly to visit_FunctionDef, since async definitions follow the
        same CLASP 3.1.1 naming rules as synchronous functions and require no special
        treatment beyond the standard validation pipeline.

        :param node: The AsyncFunctionDef AST node representing the async function definition.
        :type node: ast.AsyncFunctionDef
        """
        # Delegate to the standard function definition visitor.
        self.visit_FunctionDef(node)
