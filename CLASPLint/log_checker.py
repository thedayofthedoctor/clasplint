"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.log_checker — Validates log message usage against CLASP 3.0 conventions for pre-defined variables and exception chains.

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
from typing import List, Optional, Set

from .reporter import Violation

# Define the set of recognized logging method names.
methods_logging: Set[str] = {"debug", "info", "warning", "error", "critical", "exception"}

# Define common logging module and logger variable aliases.
names_logmodule: Set[str] = {"logging", "logger", "log", "_logger", "__logger"}


class LogChecker(ast.NodeVisitor):
    """
    Walks the AST and validates log message usage against CLASP 3.0 conventions for pre-defined variables and exception chains.

    Public methods:
        visit_Call — Detects inline string literals in logging calls and checks for missing exc_info on error-level calls.
        visit_Try — Checks try-except handlers for proper logging and re-raise patterns in exception chains.

    Private methods:
        _init_source_line_function_ — Retrieves the source line text for a given AST node.
        _init_add_violation_function_ — Records a log-related violation with full source context.
        _init_log_method_function_ — Identifies whether a function call is a recognized logging method invocation.
        _init_name_string_function_ — Extracts a dotted name string from an AST node for logger object resolution.
        _init_handler_raise_function_ — Determines whether an exception handler re-raises the caught exception.
    """

    def __init__(self, string_filepath: str, list_sourcelines: List[str]):
        """
        Initialize the log checker with file path and source lines for context.

        Stores the file path and source lines for later use during AST traversal
        and initializes an empty violations list to collect detected issues.

        :param string_filepath: Path to the file being checked for log violations.
        :type string_filepath: str
        :param list_sourcelines: Source lines of the file for contextual violation messages.
        :type list_sourcelines: List[str]
        """
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store source lines for contextual violation messages.
        self.list_sourcelines = list_sourcelines
        # Collect violations found during AST traversal.
        self.list_violations: List[Violation] = []

    def _init_source_line_function_(self, node: ast.AST) -> str:
        """
        Retrieve the source line text for a given AST node.

        Uses the node's line number to index into the stored source lines list.
        Returns the full source line text for violation context messages.

        :param node: The AST node whose source line text is needed.
        :type node: ast.AST
        :return: The source line text corresponding to the node, or an empty string.
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
        Record a log-related violation with source context.

        Constructs a Violation data class instance using the file path, node line
        number, the log category identifier, the human-readable message, and the
        extracted source line, then appends it to the internal violations list.

        :param node: The AST node at which the violation was detected.
        :type node: ast.AST
        :param string_message: The human-readable message describing the violation.
        :type string_message: str
        """
        # Append a new Violation to the violations list with full context.
        self.list_violations.append(Violation(
            # Supply the file path where the violation was detected.
            string_filepath=self.string_filepath,
            # Supply the line number of the offending logging call.
            int_linenumber=node.lineno,
            # Supply the log violation category identifier.
            string_category="log",
            # Supply the human-readable violation message.
            string_message=string_message,
            # Supply the source line for contextual display.
            string_sourceline=self._init_source_line_function_(node),
        # Close the Violation data class instantiation.
        ))

    def visit_Call(self, node: ast.Call) -> None:
        """
        Check logging calls for inline string messages and missing exc_info.

        Inspects the first positional argument of recognized logging calls to
        detect inline string literals, f-strings, or percent-formatted strings.
        For error, critical, and exception calls, it also verifies that
        exc_info=True is present to preserve full tracebacks.

        :param node: The function call AST node to inspect for logging violations.
        :type node: ast.Call
        """
        # Identify whether this call is a recognized logging method invocation.
        string_logmethod = self._init_log_method_function_(node)
        # Skip non-logging calls.
        if string_logmethod is None:
            # Continue visiting child nodes for non-logging calls.
            self.generic_visit(node)
            # Exit the visitor early for non-logging calls.
            return
        # Check if the first argument is an inline string literal.
        if node.args:
            # Get the first positional argument.
            node_firstarg = node.args[0]
            # Detect inline plain string literals in log calls.
            if isinstance(node_firstarg, ast.Constant) and isinstance(node_firstarg.value, str):
                # Record a violation for inline string in log message.
                self._init_add_violation_function_(
                    # Pass the AST node for line number extraction.
                    node,
                    # Build the violation message with the truncated string literal.
                    f"Log message must be pre-defined as a variable, not an inline "
                    # Append the log method and truncated content for context.
                    f"string literal. Call: {string_logmethod}('{node_firstarg.value[:40]}...')"
                # Close the violation function call.
                )
            # Detect inline f-strings in log calls.
            elif isinstance(node_firstarg, ast.JoinedStr):
                # Record a violation for inline f-string in log message.
                self._init_add_violation_function_(
                    # Pass the AST node for line number extraction.
                    node,
                    # Build the violation message indicating f-string usage.
                    f"Log message must be pre-defined as a variable, not an inline "
                    # Append the log method name for context.
                    f"f-string. Call: {string_logmethod}(f'...')"
                # Close the violation function call.
                )
            # Detect inline percent-formatted strings in log calls.
            elif isinstance(node_firstarg, ast.BinOp) and isinstance(node_firstarg.op, ast.Mod):
                # Record a violation for inline format string in log message.
                self._init_add_violation_function_(
                    # Pass the AST node for line number extraction.
                    node,
                    # Build the violation message indicating percent formatting.
                    f"Log message must be pre-defined as a variable, not an inline "
                    # Append the log method name and format indicator for context.
                    f"format string. Call: {string_logmethod}(... % ...)"
                # Close the violation function call.
                )
        # Build a dictionary of keyword argument names for quick lookup.
        dict_keywords = {kw.arg: kw for kw in node.keywords}
        # Check that error-level log calls include exc_info=True for traceback preservation.
        if string_logmethod in ("error", "critical", "exception"):
            # Verify the exc_info keyword argument is present.
            if "exc_info" not in dict_keywords:
                # Record a violation for missing exc_info on error log call.
                self._init_add_violation_function_(
                    # Pass the AST node for line number extraction.
                    node,
                    # Build the violation message about missing exc_info parameter.
                    f"Log call '{string_logmethod}' should include exc_info=True to "
                    # Complete the message explaining the purpose of exc_info.
                    f"preserve the full traceback."
                # Close the violation function call.
                )
        # Continue visiting child nodes.
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """
        Check try-except blocks for proper logging in exception handlers.

        Walks each exception handler body looking for logging calls and re-raise
        statements. Reports a violation when an except handler silently passes
        without either logging the error or re-raising the exception.

        :param node: The try-except AST node to inspect for logging in handlers.
        :type node: ast.Try
        """
        # Track whether any handler contains a logging call.
        bool_haslog = False
        # Inspect each exception handler for logging and re-raise patterns.
        for node_handler in node.handlers:
            # Walk the handler body looking for logging calls at any depth.
            for node_stmt in ast.walk(node_handler):
                # Check if this statement is a logging call.
                if isinstance(node_stmt, ast.Call):
                    # Identify the logging method if this is a log call.
                    string_method = self._init_log_method_function_(node_stmt)
                    # Mark that logging was found in this handler.
                    if string_method:
                        # Set the flag to indicate logging is present.
                        bool_haslog = True
                        # Exit the inner walk loop once a log call is found.
                        break
            # Determine whether the handler re-raises the exception.
            bool_reraises = self._init_handler_raise_function_(node_handler)
            # Report a violation for handlers that silently pass without logging.
            if not bool_haslog and not bool_reraises:
                # Check if the handler body is a bare 'pass' statement.
                if len(node_handler.body) == 1 and isinstance(node_handler.body[0], ast.Pass):
                    # Record a violation for a silent except handler.
                    self._init_add_violation_function_(
                        # Pass the handler AST node for line number extraction.
                        node_handler,
                        # Build the violation message about missing logging in except.
                        "Except handler silently passes without logging. "
                        # Complete the message with the requirement for logging.
                        "Every except block must log the error."
                    # Close the violation function call.
                    )
        # Continue visiting child nodes.
        self.generic_visit(node)

    def _init_log_method_function_(self, node: ast.Call) -> Optional[str]:
        """
        Return the log method name if this call is a logging invocation, else None.

        Checks whether the function call is an attribute access on a recognized
        logger variable (e.g., logger.error) or a nested attribute like self.logger.
        Returns the method name only if both the object and method are recognized.

        :param node: The function call AST node to check for logging method patterns.
        :type node: ast.Call
        :return: The logging method name if recognized, otherwise None.
        :rtype: Optional[str]
        """
        # Check for the logger.method(...) attribute call pattern.
        if isinstance(node.func, ast.Attribute):
            # Verify the attribute name is a recognized logging method.
            if node.func.attr in methods_logging:
                # Extract the object name from the attribute's value.
                node_object = node.func.value
                # Get the string representation of the object name.
                string_objname = self._init_name_string_function_(node_object)
                # Check if the object name matches a known logger variable.
                if string_objname and string_objname in names_logmodule:
                    # Return the recognized logging method name.
                    return node.func.attr
                # Also accept self.logger and self._logger attribute chains.
                if isinstance(node_object, ast.Attribute):
                    # Check if the nested attribute is a logger name.
                    if node_object.attr in names_logmodule:
                        # Return the attribute name for nested logger references.
                        return node.func.attr
        # Return None if this is not a recognized logging call.
        return None

    def _init_name_string_function_(self, node: ast.AST) -> Optional[str]:
        """
        Extract a dotted name string from an AST node.

        Returns the identifier for simple Name nodes and the attribute name for
        Attribute nodes. Used as a helper to resolve logger object references.

        :param node: The AST node from which to extract the name string.
        :type node: ast.AST
        :return: The extracted name string, or None if the node type is unsupported.
        :rtype: Optional[str]
        """
        # Return the identifier for simple Name nodes.
        if isinstance(node, ast.Name):
            # Return the identifier string for Name nodes.
            return node.id
        # Return the attribute name for Attribute nodes.
        if isinstance(node, ast.Attribute):
            # Return the attribute string for Attribute nodes.
            return node.attr
        # Return None for unsupported node types.
        return None

    def _init_handler_raise_function_(self, node_handler: ast.ExceptHandler) -> bool:
        """
        Determine whether an exception handler re-raises the caught exception.

        Scans the handler body statements for a bare raise statement (one with
        no exception argument), which indicates the caught exception is being
        propagated upward.

        :param node_handler: The exception handler AST node to inspect for a bare raise.
        :type node_handler: ast.ExceptHandler
        :return: True if the handler contains a bare raise, otherwise False.
        :rtype: bool
        """
        # Inspect each statement in the handler body for a re-raise.
        for node_stmt in node_handler.body:
            # Detect bare 'raise' statements that re-raise the current exception.
            if isinstance(node_stmt, ast.Raise):
                # A bare raise (no exception argument) re-raises the active exception.
                if node_stmt.exc is None:
                    # Confirm that a bare raise was found in the handler.
                    return True
        # No re-raise statement found in the handler body.
        return False
