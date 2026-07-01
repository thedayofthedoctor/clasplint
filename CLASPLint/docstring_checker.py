# -*- coding: utf-8 -*-
"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.docstring_checker -- Checks functions, methods, classes per CLASP 3.1.1 docstring rules.

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
import re
from typing import List, Union, Set

from .naming_utils import abbreviations_forbidden
from .reporter import Violation

# Define the set of parameter names exempt from docstring directive requirements.
parameters_exemptfromdocstring: Set[str] = {"self", "cls"}

# Words exempt from abbreviation checking: Sphinx directives, logging keywords, specialized terms.
words_techexempt: Set[str] = {
    # Sphinx directive keywords that match abbreviation patterns.
    "param", "type", "return", "rtype",
    # Python/logging technical terms that match abbreviation patterns.
    "exc", "info", "debug", "error", "critical",
    # Standard Python/CLASP pattern words used in method name descriptions.
    "init", "var", "lang", "fmt", "chk", "qual", "comm",
    # Close the technical word exemption set.
}


class DocstringChecker(ast.NodeVisitor):
    """
    Walks the AST and validates docstring presence, Sphinx format, file-level format,
    class method listing format, and text quality against CLASP 3.1.1 standards.

    Public methods:
        visit_Module -- Checks that the module has a standard-format file-level docstring.
        visit_ClassDef -- Checks that a class definition has a properly formatted docstring.
        visit_FunctionDef -- Checks function/method docstrings for Sphinx directive format.
        visit_AsyncFunctionDef -- Delegates to visit_FunctionDef for async docstring checking.

    Private methods:
        _init_source_line_function_ -- Retrieves the source line text for a given AST node.
        _init_add_violation_function_ -- Records a docstring violation with full source context.
        _init_check_format_function_ -- Validates method docstring has matching Sphinx directives.
        _init_check_detail_function_ -- Validates docstring detail between summary and directives.
        _init_scan_docstring_function_ -- Checks docstring Sphinx directives match signature.
        _init_scan_mod_docs_function_ -- Checks file-level docstring against CLASP 3.1.1 format.
        _init_chk_class_fmt_function_ -- Validates class docstring lists public and private methods.
        _init_chk_doc_qual_function_ -- Checks docstring capitalization, punctuation, abbreviations.
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
        int_lineno = getattr(node, 'lineno', 0)
        # Guard against AST nodes that lack a line number attribute.
        if int_lineno and int_lineno <= len(self.list_sourcelines):
            # Retrieve and return the corresponding source line text.
            return self.list_sourcelines[int_lineno - 1]
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
        # Use line number 1 as the default for nodes without a lineno attribute.
        int_linenumber = node.lineno if hasattr(node, 'lineno') and node.lineno else 1
        # Append a new Violation to the violations list with full context.
        self.list_violations.append(
            # Construct a new Violation instance with the detected issue details.
            Violation(
                # Supply the file path where the missing docstring was detected.
                string_filepath=self.string_filepath,
                # Supply the line number of the function or class definition.
                int_linenumber=int_linenumber,
                # Supply the docstring violation category identifier.
                string_category="docstring",
                # Supply the human-readable missing-docstring message.
                string_message=string_message,
                # Supply the source line for contextual display.
                string_sourceline=string_sourceline,
                # Close the Violation data class instantiation.
            )
        )

    def visit_Module(self, node: ast.Module) -> None:
        """
        Check the module for a CLASP 3.1.1 standard-format file-level docstring.

        Validates that the module has a docstring and that it follows the required
        format: project attribution line, module path and description, author and
        version metadata, license statement, and full GPL license text.

        :param node: The Module AST node representing the entire source file.
        :type node: ast.Module
        """
        # Retrieve the module-level docstring, or None if absent.
        string_docstring = ast.get_docstring(node)
        # Record a violation when the file-level docstring is missing entirely.
        if not string_docstring:
            # Record a violation for the missing file docstring.
            self._init_add_violation_function_(
                # Pass the module node for line number extraction.
                node,
                # Build the message indicating the missing file docstring.
                "File is missing a CLASP 3.1.1 standard-format file docstring.",
                # Close the violation function call.
            )
        # Validate the file docstring format when it is present.
        else:
            # Delegate to the file docstring format validation method.
            self._init_scan_mod_docs_function_(node, string_docstring)
        # Validate docstring text quality for the file docstring.
        if string_docstring:
            # Delegate to the docstring text quality validation method.
            self._init_chk_doc_qual_function_(node, string_docstring, "File")
        # Continue visiting child nodes for class and function checks.
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Check the class docstring, validate its format, and then visit child nodes for methods.

        Classes require a presence check and format validation per CLASP 3.1.1.
        The class docstring must include a brief description and list of public
        and private methods.

        :param node: The class definition AST node being visited.
        :type node: ast.ClassDef
        """
        # Retrieve the class docstring, or None if absent.
        string_docstring = ast.get_docstring(node)
        # Record a violation when the class docstring is missing.
        if not string_docstring:
            # Record a violation for the missing class docstring.
            self._init_add_violation_function_(
                # Pass the class definition node for line number extraction.
                node,
                # Build the message identifying the class missing a docstring.
                f"Class '{node.name}' is missing a docstring.",
                # Close the violation function call.
            )
        # Validate the class docstring format when it is present.
        else:
            # Delegate to the class docstring format validation method.
            self._init_chk_class_fmt_function_(node, string_docstring)
            # Validate docstring text quality for the class docstring.
            self._init_chk_doc_qual_function_(
                # Pass the class definition node.
                node,
                # Pass the docstring text.
                string_docstring,
                # Pass the display name for violation messages.
                f"Class '{node.name}'"
                # Close the quality check function call.
            )
        # Save the previous class context before entering the new class.
        string_previous = self.string_currentclass
        # Set the current class name for method context messages.
        self.string_currentclass = node.name
        # Visit child nodes within the class body to check methods.
        self.generic_visit(node)
        # Restore the previous class context after leaving the class.
        self.string_currentclass = string_previous

    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
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
        # Validate docstring text quality for all functions and methods.
        self._init_chk_doc_qual_function_(node, string_docstring, string_displayname)
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
            self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
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
        :type node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
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
            self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
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
        # A multisection docstring needs at least 3 lines: summary, blank, and one detail line.
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
            if (string_line.startswith(":param") or string_line.startswith(":return")
                    # Also match :type and :rtype Sphinx directives to stop scanning.
                    or string_line.startswith(":type") or string_line.startswith(":rtype")):
                # Stop scanning once directives begin.
                break
            # A non-blank, non-directive line counts as detailed description content.
            if (string_line and not string_line.startswith(":param")
                    # Exclude lines that start with any Sphinx directive keyword.
                    and not string_line.startswith(":return")
                    # Exclude lines that start with :type to keep only prose content.
                    and not string_line.startswith(":type")
                    # Exclude lines that start with :rtype to finalize the prose filter.
                    and not string_line.startswith(":rtype")):
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

        # Mark this method as static since it only operates on the provided docstring.
    @staticmethod
    def _init_scan_docstring_function_(string_docstring: str):
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

    def _init_scan_mod_docs_function_(self, node: ast.Module, string_docstring: str) -> None:
        """
        Validate the file-level docstring against CLASP 3.1.1 format requirements.

        Checks that the file docstring contains the required sections: the project
        attribution line in uppercase, module path and description, author and version
        metadata, license statement, and the full GPL license text.

        :param node: The Module AST node for line number extraction.
        :type node: ast.Module
        :param string_docstring: The file-level docstring text to validate.
        :type string_docstring: str
        """
        # Split the docstring into individual lines for section analysis.
        list_lines = string_docstring.splitlines()
        # A valid file docstring must have at least 3 lines.
        if len(list_lines) < 3:
            # Record a violation for file docstrings that are too short.
            self._init_add_violation_function_(
                # Pass the module node.
                node,
                # Build the message about the incomplete file docstring.
                "File docstring is incomplete; must include project attribution, "
                # Complete the message with the required sections.
                "module description, author metadata, and license text."
                # Close the violation function call.
            )
            # Exit early since the docstring is too short to analyze further.
            return
        # Check that the first line starts with "THIS FILE IS PART OF" in uppercase.
        if not list_lines[0].strip().startswith("THIS FILE IS PART OF"):
            # Record a violation for missing project attribution line.
            self._init_add_violation_function_(
                # Pass the module node.
                node,
                # Build the message about the missing attribution line.
                "File docstring first line must start with "
                # Append the expected template format for the first line of a file docstring.
                "'THIS FILE IS PART OF <project> BY <author>'."
                # Close the violation function call.
            )
        # Check that the second line contains the module path and description.
        if len(list_lines) > 1:
            # The second line should not be blank and should describe the module.
            if not list_lines[1].strip():
                # Record a violation for a blank second line.
                self._init_add_violation_function_(
                    # Pass the module node.
                    node,
                    # Build the message about the module description line.
                    "File docstring second line must contain '<module_path> -- <description>'."
                    # Close the violation function call.
                )
        # Track whether the license statement was found.
        bool_haslicense = False
        # Track whether the copyright line was found.
        bool_hascopyright = False
        # Scan the remaining lines for license and copyright information.
        for string_line in list_lines[2:]:
            # Detect the license statement line.
            if "THIS PROGRAM IS LICENSED UNDER" in string_line:
                # Mark that the license statement was found.
                bool_haslicense = True
            # Detect the copyright line.
            if string_line.strip().startswith("Copyright (C)"):
                # Mark that the copyright line was found.
                bool_hascopyright = True
        # Report a violation when the license statement is missing.
        if not bool_haslicense:
            # Record a violation for missing license statement.
            self._init_add_violation_function_(
                # Pass the module node.
                node,
                # Build the message about the missing license statement.
                "File docstring must contain 'THIS PROGRAM IS LICENSED UNDER <license>' line."
                # Close the violation function call.
            )
        # Report a violation when the copyright line is missing.
        if not bool_hascopyright:
            # Record a violation for missing copyright line.
            self._init_add_violation_function_(
                # Pass the module node.
                node,
                # Build the message about the missing copyright line.
                "File docstring must contain a 'Copyright (C) <year> <author>' line."
                # Close the violation function call.
            )

    def _init_chk_class_fmt_function_(self, node: ast.ClassDef, string_docstring: str) -> None:
        """
        Validate that a class docstring lists public and private methods.

        Checks that the class docstring contains "Public methods:" and
        "Private methods:" sections as required by CLASP 3.1.1.

        :param node: The ClassDef AST node for line number extraction.
        :type node: ast.ClassDef
        :param string_docstring: The class docstring text to validate.
        :type string_docstring: str
        """
        # Check for the presence of the Public methods section.
        if "Public methods:" not in string_docstring:
            # Record a violation for missing Public methods section.
            self._init_add_violation_function_(
                # Pass the class definition node.
                node,
                # Build the message about the missing Public methods section.
                f"Class '{node.name}' docstring must contain a 'Public methods:' section."
                # Close the violation function call.
            )
        # Check for the presence of the Private methods section.
        if "Private methods:" not in string_docstring:
            # Record a violation for missing Private methods section.
            self._init_add_violation_function_(
                # Pass the class definition node.
                node,
                # Build the message about the missing Private methods section.
                f"Class '{node.name}' docstring must contain a 'Private methods:' section."
                # Close the violation function call.
            )

    def _init_chk_doc_qual_function_(
            # Accept the AST node for line-number extraction in violation reports.
            self, node: ast.AST, string_docstring: str,
            # Accept a display name string for use in human-readable violation messages.
            string_displayname: str
            # Complete the method signature with no return annotation requirement.
    ) -> None:
        """
        Validate docstring text quality: capitalization, punctuation, and abbreviations.

        Sphinx directive lines are excluded from abbreviation and quality checks.
        Three phases: summary validation, prose filtering, abbreviation scanning.

        :param node: The AST node for line number extraction.
        :type node: ast.AST
        :param string_docstring: The docstring text to validate.
        :type string_docstring: str
        :param string_displayname: The human-readable name for violation messages.
        :type string_displayname: str
        """
        # Split the docstring into individual lines for analysis.
        list_lines = string_docstring.splitlines()
        # Skip quality check for empty docstrings.
        if not list_lines:
            # Exit early for empty docstrings.
            return
        # Phase 1: extract and validate the summary paragraph.
        string_summary = self._init_ext_summary_function_(list_lines)
        # Validate summary capitalization and punctuation when present.
        if string_summary and not string_summary.isupper():
            # Check that the summary starts with a capital letter.
            if string_summary[0].islower():
                # Record a violation for lowercase start.
                self._init_add_violation_function_(
                    # Pass the AST node for accurate line-number reporting.
                    node,
                    # Provide the capitalization violation message with a truncated summary.
                    f"{string_displayname} docstring summary must start with a capital letter. "
                    # Append a truncated preview of the offending summary text.
                    f"Found: '{string_summary[:40]}...'"
                )
            # Check that the summary ends with proper sentence-ending punctuation.
            if not string_summary.endswith(('.', '!', '?')):
                # Record a violation for missing terminal punctuation.
                self._init_add_violation_function_(
                    # Pass the AST node for accurate line-number reporting.
                    node, f"{string_displayname} docstring summary must end with a period. "
                    # Append a truncated preview of the offending summary text.
                          f"Found: '{string_summary[:40]}...'"
                )
        # Phase 2 & 3: filter prose and check abbreviations, using packed state for fewer locals.
        tuple_abbrevstate = ([], set())
        # Iterate over each line in the docstring to check for abbreviations.
        for string_line in list_lines:
            # Get the trimmed version of the current line.
            string_trimmed = string_line.strip()
            # Skip Sphinx directive lines from abbreviation checking.
            if string_trimmed.startswith((":param", ":type", ":return", ":rtype")):
                # Continue to the next line, excluding directive lines.
                continue
            # Include non-directive lines for abbreviation checking.
            tuple_abbrevstate[0].append(string_trimmed)
        # Join prose lines and tokenize words for abbreviation detection.
        string_prose = " ".join(tuple_abbrevstate[0])
        # Find all alphabetic word tokens in the prose text.
        list_words = re.findall(r'[a-zA-Z]+', string_prose)
        # Scan each word token for forbidden abbreviations.
        for string_word in list_words:
            # Convert to lowercase for dictionary lookup.
            string_lower = string_word.lower()
            # Skip words not in the abbreviation dictionary or already reported.
            if string_lower not in abbreviations_forbidden or string_lower in tuple_abbrevstate[1]:
                # Continue to the next word if not a forbidden unreported abbreviation.
                continue
            # Exempt technical terms and CLASP-private-method names.
            if string_lower in words_techexempt or string_lower == "init":
                # Continue without flagging exempt technical vocabulary.
                continue
            # Mark this abbreviation as reported to avoid duplicate violations.
            tuple_abbrevstate[1].add(string_lower)
            # Skip abbreviations that appear only in class method-listing sections.
            if self._init_chk_meth_list_function_(list_lines, string_word):
                # Continue without flagging method-name abbreviations.
                continue
            # Record a violation for the forbidden abbreviation.
            self._init_add_violation_function_(
                # Pass the AST node for accurate line-number reporting.
                node, f"{string_displayname} docstring contains abbreviated word "
                # Append the detected abbreviation and its recommended full replacement.
                      f"'{string_word}' (use '{abbreviations_forbidden[string_lower]}' instead)."
            )

    # Mark this method as static since it only operates on the provided line list.
    @staticmethod
    def _init_ext_summary_function_(list_lines: list) -> str:
        """
        Extract the first non-blank, non-Sphinx-directive paragraph as the summary.

        Collects consecutive non-blank, non-directive lines until a blank line or
        Sphinx directive is encountered, then joins them with spaces.

        :param list_lines: The docstring split into individual lines.
        :type list_lines: list
        :return: The joined summary paragraph string, or an empty string if none found.
        :rtype: str
        """
        # Collect lines of the first paragraph (until blank line or directive).
        list_summarylines = []
        # Iterate over lines to find the first paragraph.
        for string_line in list_lines:
            # Get the trimmed version of the current line.
            string_trimmed = string_line.strip()
            # A blank line after collecting summary lines marks the end.
            if not string_trimmed:
                # Exit the paragraph loop when a blank separator is found.
                if list_summarylines:
                    # Terminate the summary extraction loop immediately.
                    break
                # Continue past leading blank lines.
                continue
            # Stop at Sphinx directive lines.
            if string_trimmed.startswith((":param", ":type", ":return", ":rtype")):
                # Exit the paragraph loop when directives begin.
                if list_summarylines:
                    # Terminate the summary extraction loop at the directive boundary.
                    break
            # Add this line to the summary paragraph.
            list_summarylines.append(string_trimmed)
        # Join all summary paragraph lines with a space.
        return " ".join(list_summarylines)

    # Mark this method as static since it checks word presence without instance state.
    @staticmethod
    def _init_chk_meth_list_function_(list_lines: list, string_word: str) -> bool:
        """
        Determine whether a word appears inside a class method-listing section.

        Method listings in class docstrings use an indented pattern with a dash
        separator and are exempt from abbreviation checks because they contain
        CLASP-compliant private method names.

        :param list_lines: The docstring split into individual lines.
        :type list_lines: list
        :param string_word: The word to search for in method listing lines.
        :type string_word: str
        :return: True if the word is found inside a method listing line.
        :rtype: bool
        """
        # Iterate over docstring lines to check for method listing patterns.
        for string_line in list_lines:
            # Detect method listing lines by their indented name-and-dash pattern.
            if string_word in string_line and re.match(r'^\s+\w+.*--', string_line):
                # Confirm that the word is part of a method listing entry.
                return True
        # The word was not found in any method listing line.
        return False
