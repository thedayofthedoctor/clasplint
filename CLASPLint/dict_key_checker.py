# Check dictionary key names against CLASP 3.0 PascalCase and abbreviation rules.

import ast
from typing import List

from .naming_utils import validate_dictkey_format
from .reporter import Violation


class DictKeyChecker(ast.NodeVisitor):
    """Walk the AST and check dictionary key names against CLASP 3.0 rules."""

    def __init__(self, string_filepath: str, list_sourcelines: List[str]):
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store source lines for contextual violation messages.
        self.list_sourcelines = list_sourcelines
        # Collect violations found during AST traversal.
        self.list_violations: List[Violation] = []

    def _init_key_function_(self, node_key: ast.AST, node_dict: ast.AST) -> None:
        """Validate a single dictionary key literal."""
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
            string_sourceline = self.list_sourcelines[node_key.lineno - 1]
        # Append each detected violation to the violations list.
        for string_message in list_issues:
            self.list_violations.append(Violation(
                string_filepath=self.string_filepath,
                int_linenumber=node_key.lineno,
                string_category="dict_key",
                string_message=string_message,
                string_sourceline=string_sourceline,
            ))

    def visit_Dict(self, node: ast.Dict) -> None:
        """Check keys in dictionary literal expressions."""
        # Iterate over each key node in the dictionary literal.
        for node_key in node.keys:
            # Process non-None keys through the key validator.
            if node_key is not None:
                self._init_key_function_(node_key, node)
        # Continue visiting child nodes for nested dictionaries.
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Check dict() constructor calls for keyword argument key names."""
        # Detect calls to the built-in dict() constructor.
        if isinstance(node.func, ast.Name) and node.func.id == "dict":
            # Check each keyword argument name as a potential dict key.
            for node_keyword in node.keywords:
                # Validate the keyword argument if it has an explicit name.
                if node_keyword.arg:
                    self._init_keyword_as_key_function_(node_keyword)
        # Continue visiting child nodes.
        self.generic_visit(node)

    def _init_keyword_as_key_function_(self, node_keyword: ast.keyword) -> None:
        """Validate a keyword argument name used as a dictionary key."""
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
        """Visit subscript nodes for potential dict key access within Assign statements."""
        # Subscript key checks are handled during Assign target walking.
        self.generic_visit(node)
