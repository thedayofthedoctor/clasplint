# -*- coding: utf-8 -*-
"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.runner -- orchestrates all CLASP 3.1.1 checkers across files and directories.

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
import os
from typing import List

from .variable_checker import VariableChecker
from .dict_key_checker import DictKeyChecker
from .function_checker import FunctionChecker
from .comment_checker import CommentChecker
from .log_checker import LogChecker
from .docstring_checker import DocstringChecker
from .reporter import Report


def _init_run_ast_function_(tree: ast.Module, string_filepath: str,
                              # Accept the list of source lines for contextual violation display.
                              list_sourcelines: List[str],
                              # Receive the report object to aggregate all detected violations.
                              report_result: Report) -> None:
    """Run all AST-based checkers on a successfully parsed syntax tree."""
    # Check variable names against CLASP 3.1.1 rules.
    checker_variable = VariableChecker(string_filepath, list_sourcelines)
    # Traverse the AST with the variable checker.
    checker_variable.visit(tree)
    # Transfer variable violations to the report.
    for violation_item in checker_variable.list_violations:
        # Record each variable violation in the aggregate report.
        report_result.record(violation_item)
    # Check dictionary key names against CLASP 3.1.1 rules.
    checker_dictkey = DictKeyChecker(string_filepath, list_sourcelines)
    # Traverse the AST with the dict key checker.
    checker_dictkey.visit(tree)
    # Transfer dict key violations to the report.
    for violation_item in checker_dictkey.list_violations:
        # Record each dictionary key violation in the aggregate report.
        report_result.record(violation_item)
    # Check function and class names against CLASP 3.1.1 rules.
    checker_function = FunctionChecker(string_filepath, list_sourcelines)
    # Traverse the AST with the function checker.
    checker_function.visit(tree)
    # Transfer function violations to the report.
    for violation_item in checker_function.list_violations:
        # Record each function or class violation in the aggregate report.
        report_result.record(violation_item)
    # Check log message conventions against CLASP 3.1.1 rules.
    checker_log = LogChecker(string_filepath, list_sourcelines)
    # Traverse the AST with the log checker.
    checker_log.visit(tree)
    # Transfer log violations to the report.
    for violation_item in checker_log.list_violations:
        # Record each log message violation in the aggregate report.
        report_result.record(violation_item)
    # Check function and class docstrings against CLASP 3.1.1 best practices.
    checker_docstring = DocstringChecker(string_filepath, list_sourcelines)
    # Traverse the AST with the docstring checker.
    checker_docstring.visit(tree)
    # Transfer docstring violations to the report.
    for violation_item in checker_docstring.list_violations:
        # Record each missing-docstring violation in the aggregate report.
        report_result.record(violation_item)


def analyze_file(string_filepath: str) -> Report:
    """
    Run all CLASP 3.1.1 checkers on a single Python file and return a Report.

    Reads the file, parses an AST, runs AST-based checkers inside a try block,
    and unconditionally runs the token-based comment checker afterward. Files
    that cannot be read return an empty report; syntax errors silently skip AST
    checks but still allow the comment checker to execute.

    :param string_filepath: Absolute or relative path to the Python file to analyze.
    :type string_filepath: str
    :return: A Report containing all violations found in the file.
    :rtype: Report
    """
    # Initialize an empty report for this file.
    report_result = Report()
    # Mark that one file is being checked.
    report_result.int_fileschecked = 1
    # Attempt to read the file contents with UTF-8 encoding.
    try:
        # Open the file for reading.
        with open(string_filepath, "r", encoding="utf-8") as file_handle:
            # Read the entire file content as a string.
            string_source = file_handle.read()
    # Handle file read errors by returning an empty report.
    except (IOError, UnicodeDecodeError):
        # Return the empty report if the file cannot be read.
        return report_result
    # Return the empty report for empty files.
    if not string_source.strip():
        # Exit early for files with no content to check.
        return report_result
    # Split the source into lines for per-line access by checkers.
    list_sourcelines = string_source.splitlines()
    # Attempt to parse and run AST-based checkers.
    try:
        # Parse the source code into an abstract syntax tree.
        tree = ast.parse(string_source, filename=string_filepath)
        # Run all AST-based checkers on the freshly parsed tree.
        _init_run_ast_function_(tree, string_filepath, list_sourcelines, report_result)
    # Skip AST-based checkers when syntax errors prevent parsing.
    except SyntaxError:
        # AST checks are silently skipped for syntax-error files; the comment checker still runs.
        report_result.int_fileschecked = report_result.int_fileschecked
    # Run token-based comment checker (works even on syntax errors).
    checker_comment = CommentChecker(string_filepath, string_source)
    # Execute all comment format and presence checks.
    checker_comment.run()
    # Transfer comment violations to the report.
    for violation_item in checker_comment.list_violations:
        # Record each comment format violation in the aggregate report.
        report_result.record(violation_item)
    # Mark the file as having violations if any were found.
    if report_result.list_violations:
        # Increment the files-with-violations counter for this file.
        report_result.int_fileswithviolations = 1
    # Return the completed report for this file.
    return report_result


def analyze_directory(string_directory: str, bool_recursive: bool = True) -> Report:
    """
    Run all CLASP 3.1.1 checkers on every Python file in a directory tree.

    Walks the directory, discovers all .py files, calls analyze_file on each,
    and merges the resulting Reports into a single aggregate Report. When
    bool_recursive is False, only the top-level directory is processed.

    :param string_directory: Absolute or relative path to the directory to scan.
    :type string_directory: str
    :param bool_recursive: Whether to descend into subdirectories.
    :type bool_recursive: bool
    :return: A merged Report aggregating violations from all discovered .py files.
    :rtype: Report
    """
    # Initialize an empty aggregate report for the directory.
    report_result = Report()
    # Walk the directory tree to discover Python files.
    for string_root, list_subdirectories, list_files in os.walk(string_directory):
        # Exclude hidden and virtual environment directories from traversal.
        list_subdirectories[:] = [d for d in list_subdirectories
                                    # Keep directories that are not hidden.
                                    if not d.startswith(".")
                                    # Exclude virtual environment and build artifact directories.
                                    and d not in ("__pycache__", "venv", ".venv", "env",
                                                   # Additional excluded directory names.
                                                   ".env", "node_modules", ".git", "dist",
                                                   # Build-related directories to skip.
                                                   "build", ".tox", ".eggs")]
        # Sort the file list for deterministic processing order.
        for string_filename in sorted(list_files):
            # Only process files with the .py extension.
            if string_filename.endswith(".py"):
                # Build the absolute file path for analysis.
                string_filepath = os.path.join(string_root, string_filename)
                # Run all checkers on this Python file.
                report_file = analyze_file(string_filepath)
                # Accumulate the files-checked count from this file.
                report_result.int_fileschecked += report_file.int_fileschecked
                # Accumulate the files-with-violations count from this file.
                report_result.int_fileswithviolations += report_file.int_fileswithviolations
                # Merge violations from this file into the directory report.
                for violation_item in report_file.list_violations:
                    # Record each violation from the file in the aggregate report.
                    report_result.record(violation_item)
        # Stop descending into subdirectories when recursive mode is disabled.
        if not bool_recursive:
            # Prevent os.walk from yielding any deeper directory levels.
            list_subdirectories.clear()
    # Return the aggregated report for the directory.
    return report_result


def run(list_paths: List[str], bool_recursive: bool = True) -> Report:
    """
    Entry point: dispatch CLASP 3.1.1 checkers across a list of files and directories.

    Iterates over each path, delegates to analyze_file for individual files and
    analyze_directory for directories, then merges all Reports into one aggregate.

    :param list_paths: List of absolute paths to Python files or directories.
    :type list_paths: List[str]
    :param bool_recursive: Whether directories should be scanned recursively.
    :type bool_recursive: bool
    :return: A merged Report covering all paths.
    :rtype: Report
    """
    # Initialize an empty aggregate report for all paths.
    report_result = Report()
    # Process each provided path in order.
    for string_path in list_paths:
        # Determine whether the path is a directory or a file.
        if os.path.isdir(string_path):
            # Run directory-level analysis on the given path.
            report_path = analyze_directory(string_path, bool_recursive=bool_recursive)
        # Analyze individual files that are not directories.
        elif os.path.isfile(string_path):
            # Run file-level analysis on the given path.
            report_path = analyze_file(string_path)
        # Skip paths that are neither files nor directories.
        else:
            # Continue to the next path for unsupported path types.
            continue
        # Accumulate the files-checked count from this path.
        report_result.int_fileschecked += report_path.int_fileschecked
        # Accumulate the files-with-violations count from this path.
        report_result.int_fileswithviolations += report_path.int_fileswithviolations
        # Merge violations from this path into the aggregate report.
        for violation_item in report_path.list_violations:
            # Record each violation in the aggregate report.
            report_result.record(violation_item)
    # Return the aggregated report for all paths.
    return report_result
