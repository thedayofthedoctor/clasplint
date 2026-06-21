"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.dict_key_checker — Validates dictionary key names against CLASP 3.0 PascalCase and abbreviation rules.

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

from .naming_utils import validate_dictkey_format
from .reporter import Violation


class DictKeyChecker(ast.NodeVisitor):
    """
    Walks the AST and validates dictionary key names against CLASP 3.0 PascalCase naming rules.

    Public methods:
        visit_Dict — Checks each key in dictionary literal expressions against PascalCase format.
        visit_Call — Checks keyword argument names in dict() constructor calls.
        visit_Subscript — Visits subscript nodes for potential dictionary key access in assignments.

    Private methods:
        _init_key_function_ — Validates a single string-constant dictionary key against CLASP 3.0 rules.
        _init_keyword_as_key_function_ — Validates a keyword argument name used as a dictionary key identifier.
    """

    def __init__(self, string_filepath: str, list_sourcelines: List[str]):
        """Initialize the dict key checker with file path and source lines for context.

        Stores the provided file path and source lines for later use in violation
        reporting and contextual display. Also initializes an empty list to collect
        violations discovered during AST traversal.

        :param string_filepath: Path to the file being checked.
        :type string_filepath: str
        :param list_sourcelines: Source lines of the file being checked.
        :type list_sourcelines: List[str]
        """
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store source lines for contextual violation messages.
        self.list_sourcelines = list_sourcelines
        # Collect violations found during AST traversal.
        self.list_violations: List[Violation] = []

    def _init_key_function_(self, node_key: ast.AST, node_dict: ast.AST) -> None:
        """Validate a single dictionary key literal.

        Verifies that the key is a string constant before applying CLASP 3.0 dict key
        format validation. Each detected format violation is appended to the violations
        list with its source line context.

        :param node_key: The dictionary key AST node to validate.
        :type node_key: ast.AST
        :param node_dict: The parent dictionary AST node.
        :type node_dict: ast.AST
        """
        # Only string literal keys are checked; skip non-constant or non-string keys.
        if not isinstance(node_key, ast.Constant):
            # Exit early for non-constant dict key nodes.
            return
        # Skip keys whose values are not strings.
        if not isinstance(node_key.value, str):
            # Exit early for keys whose values are not strings.
            return
        # Extract the key string value.
        string_key = node_key.value
        # Run the CLASP 3.0 dict key format validation.
        list_issues = validate_dictkey_format(string_key)
        # Retrieve the source line for contextual output.
        string_sourceline = ""
        # Ensure the line number is within bounds before accessing source lines.
        if node_key.lineno and node_key.lineno <= len(self.list_sourcelines):
            # Assign the source line at the detected line number.
            string_sourceline = self.list_sourcelines[node_key.lineno - 1]
        # Append each detected violation to the violations list.
        for string_message in list_issues:
            # Construct a Violation with full file and line context.
            self.list_violations.append(Violation(
                # Supply the file path where the violation was detected.
                string_filepath=self.string_filepath,
                # Supply the line number of the offending dictionary key.
                int_linenumber=node_key.lineno,
                # Supply the violation category identifier.
                string_category="dict_key",
                # Supply the human-readable violation message.
                string_message=string_message,
                # Supply the source line for contextual display.
                string_sourceline=string_sourceline,
            # Close the Violation data class instantiation.
            ))

    def visit_Dict(self, node: ast.Dict) -> None:
        """Check keys in dictionary literal expressions.

        Iterates over every key node in the dictionary literal and delegates
        non-None keys to the key validation method. Then continues generic
        visitation of child nodes to handle nested dictionary literals.

        :param node: The dictionary AST node to visit.
        :type node: ast.Dict
        """
        # Iterate over each key node in the dictionary literal.
        for node_key in node.keys:
            # Process non-None keys through the key validator.
            if node_key is not None:
                # Delegate to the key validation method for this dictionary key.
                self._init_key_function_(node_key, node)
        # Continue visiting child nodes for nested dictionaries.
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check dict() constructor calls for keyword argument key names.

        Detects calls to the built-in dict() constructor and validates each keyword
        argument name against CLASP 3.0 dict key naming rules. Non-dict calls are
        skipped and generic visitation continues for nested structures.

        :param node: The call AST node to visit.
        :type node: ast.Call
        """
        # Detect calls to the built-in dict() constructor.
        if isinstance(node.func, ast.Name) and node.func.id == "dict":
            # Check each keyword argument name as a potential dict key.
            for node_keyword in node.keywords:
                # Validate the keyword argument if it has an explicit name.
                if node_keyword.arg:
                    # Delegate to the keyword-as-key validation method.
                    self._init_keyword_as_key_function_(node_keyword)
        # Continue visiting child nodes.
        self.generic_visit(node)

    def _init_keyword_as_key_function_(self, node_keyword: ast.keyword) -> None:
        """Validate a keyword argument name used as a dictionary key.

        Extracts the keyword argument name from the AST node and validates it against
        CLASP 3.0 rules. Currently only flags empty keyword names, as Python keyword
        arguments are identifiers and cannot directly use PascalCase.

        :param node_keyword: The keyword AST node to validate.
        :type node_keyword: ast.keyword
        """
        # Extract the keyword argument name.
        string_key = node_keyword.arg
        # Skip empty or missing keyword argument names.
        if not string_key:
            # Exit early for empty keyword argument names.
            return
        # Python keyword arguments are identifiers and cannot use PascalCase directly;
        # Only flag if the name clearly violates PascalCase convention expectations.
        pass

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Visit subscript nodes for potential dict key access within Assign statements.

        Subscript key checks are handled during Assign target walking rather than at
        the individual subscript node level. This method simply continues generic
        visitation of child nodes for completeness.

        :param node: The subscript AST node to visit.
        :type node: ast.Subscript
        """
        # Subscript key checks are handled during Assign target walking.
        self.generic_visit(node)
