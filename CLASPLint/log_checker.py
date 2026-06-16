# Check log message usage against CLASP 3.0 conventions: pre-defined variables and proper exception chains.

import ast
from typing import List, Optional, Set

from .reporter import Violation

# Define the set of recognized logging method names.
methods_logging: Set[str] = {"debug", "info", "warning", "error", "critical", "exception"}

# Define common logging module and logger variable aliases.
names_logmodule: Set[str] = {"logging", "logger", "log", "_logger", "__logger"}


class LogChecker(ast.NodeVisitor):
    """Walk the AST and check log message usage against CLASP 3.0 rules."""

    def __init__(self, string_filepath: str, list_sourcelines: List[str]):
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store source lines for contextual violation messages.
        self.list_sourcelines = list_sourcelines
        # Collect violations found during AST traversal.
        self.list_violations: List[Violation] = []

    def _init_source_line_function_(self, node: ast.AST) -> str:
        """Retrieve the source line text for a given AST node."""
        # Return the source line if the node has a valid line number within bounds.
        if node.lineno and node.lineno <= len(self.list_sourcelines):
            # Retrieve and return the corresponding source line text.
            return self.list_sourcelines[node.lineno - 1]
        # Return an empty string if the line number is unavailable or out of range.
        return ""

    def _init_add_violation_function_(self, node: ast.AST, string_message: str) -> None:
        """Record a log-related violation with source context."""
        # Append a new Violation to the violations list with full context.
        self.list_violations.append(Violation(
            string_filepath=self.string_filepath,
            int_linenumber=node.lineno,
            string_category="log",
            string_message=string_message,
            string_sourceline=self._init_source_line_function_(node),
        ))

    def visit_Call(self, node: ast.Call) -> None:
        """Check logging calls for inline string messages and missing exc_info."""
        # Identify whether this call is a recognized logging method invocation.
        string_logmethod = self._init_log_method_function_(node)
        # Skip non-logging calls.
        if string_logmethod is None:
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
                    node,
                    f"Log message must be pre-defined as a variable, not an inline "
                    f"string literal. Call: {string_logmethod}('{node_firstarg.value[:40]}...')"
                )
            # Detect inline f-strings in log calls.
            elif isinstance(node_firstarg, ast.JoinedStr):
                # Record a violation for inline f-string in log message.
                self._init_add_violation_function_(
                    node,
                    f"Log message must be pre-defined as a variable, not an inline "
                    f"f-string. Call: {string_logmethod}(f'...')"
                )
            # Detect inline percent-formatted strings in log calls.
            elif isinstance(node_firstarg, ast.BinOp) and isinstance(node_firstarg.op, ast.Mod):
                # Record a violation for inline format string in log message.
                self._init_add_violation_function_(
                    node,
                    f"Log message must be pre-defined as a variable, not an inline "
                    f"format string. Call: {string_logmethod}(... % ...)"
                )
        # Build a dictionary of keyword argument names for quick lookup.
        dict_keywords = {kw.arg: kw for kw in node.keywords}
        # Check that error-level log calls include exc_info=True for traceback preservation.
        if string_logmethod in ("error", "critical", "exception"):
            # Verify the exc_info keyword argument is present.
            if "exc_info" not in dict_keywords:
                # Record a violation for missing exc_info on error log call.
                self._init_add_violation_function_(
                    node,
                    f"Log call '{string_logmethod}' should include exc_info=True to "
                    f"preserve the full traceback."
                )
        # Continue visiting child nodes.
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Check try-except blocks for proper logging in exception handlers."""
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
                        node_handler,
                        "Except handler silently passes without logging. "
                        "Every except block must log the error."
                    )
        # Continue visiting child nodes.
        self.generic_visit(node)

    def _init_log_method_function_(self, node: ast.Call) -> Optional[str]:
        """Return the log method name if this call is a logging invocation, else None."""
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
        """Extract a dotted name string from an AST node."""
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
        """Determine whether an exception handler re-raises the caught exception."""
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
