"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.runner — orchestrates all CLASP 3.0 checkers across files and directories.

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
import os
from typing import List

from .variable_checker import VariableChecker
from .dict_key_checker import DictKeyChecker
from .function_checker import FunctionChecker
from .comment_checker import CommentChecker
from .log_checker import LogChecker
from .docstring_checker import DocstringChecker
from .reporter import Report


def analyze_file(string_filepath: str) -> Report:
    """Run all CLASP 3.0 checkers on a single Python file and return a Report."""
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
    # Attempt to parse the source into an AST for AST-based checkers.
    try:
        # Parse the source code into an abstract syntax tree.
        tree = ast.parse(string_source, filename=string_filepath)
    # Set tree to None when syntax errors prevent AST-based checking.
    except SyntaxError:
        # Assign None to indicate that AST-based checking is unavailable.
        tree = None
    # Run AST-based checkers if the tree was successfully parsed.
    if tree is not None:
        # Check variable names against CLASP 3.0 rules.
        checker_variable = VariableChecker(string_filepath, list_sourcelines)
        # Traverse the AST with the variable checker.
        checker_variable.visit(tree)
        # Transfer variable violations to the report.
        for violation_item in checker_variable.list_violations:
            # Record each variable violation in the aggregate report.
            report_result.record(violation_item)
        # Check dictionary key names against CLASP 3.0 rules.
        checker_dictkey = DictKeyChecker(string_filepath, list_sourcelines)
        # Traverse the AST with the dict key checker.
        checker_dictkey.visit(tree)
        # Transfer dict key violations to the report.
        for violation_item in checker_dictkey.list_violations:
            # Record each dictionary key violation in the aggregate report.
            report_result.record(violation_item)
        # Check function and class names against CLASP 3.0 rules.
        checker_function = FunctionChecker(string_filepath, list_sourcelines)
        # Traverse the AST with the function checker.
        checker_function.visit(tree)
        # Transfer function violations to the report.
        for violation_item in checker_function.list_violations:
            # Record each function or class violation in the aggregate report.
            report_result.record(violation_item)
        # Check log message conventions against CLASP 3.0 rules.
        checker_log = LogChecker(string_filepath, list_sourcelines)
        # Traverse the AST with the log checker.
        checker_log.visit(tree)
        # Transfer log violations to the report.
        for violation_item in checker_log.list_violations:
            # Record each log message violation in the aggregate report.
            report_result.record(violation_item)
        # Check function and class docstrings against CLASP 3.0 best practices.
        checker_docstring = DocstringChecker(string_filepath, list_sourcelines)
        # Traverse the AST with the docstring checker.
        checker_docstring.visit(tree)
        # Transfer docstring violations to the report.
        for violation_item in checker_docstring.list_violations:
            # Record each missing-docstring violation in the aggregate report.
            report_result.record(violation_item)
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
    """Run all CLASP 3.0 checkers on Python files in a directory and return an aggregated Report."""
    # Initialize an empty aggregated report.
    report_result = Report()
    # Walk the directory tree to find all Python files.
    for string_root, list_dirs, list_files in os.walk(string_directory):
        # Filter out hidden directories and common virtual environment folders.
        list_dirs[:] = [
            # Iterate over each directory in the current tree level.
            d for d in list_dirs
            # Keep only directories that are not hidden and not virtual environments.
            if not d.startswith(".")
            # Also exclude common virtual environment and build directories.
            and d not in (
                # List of common directories to exclude from traversal.
                "__pycache__", "venv", ".venv", "env",
                # Continue the exclusion list with additional patterns.
                ".env", "node_modules", ".git", "dist",
                # Complete the exclusion list with build and test directories.
                "build", ".tox", ".eggs",
            # Close the tuple of excluded directory names.
            )
        # Close the list comprehension result for directory filtering.
        ]
        # Check each Python file in the current directory.
        for string_filename in list_files:
            # Process only files with the .py extension.
            if string_filename.endswith(".py"):
                # Build the full file path.
                string_filepath = os.path.join(string_root, string_filename)
                # Run all checkers on this file.
                report_file = analyze_file(string_filepath)
                # Accumulate the file count.
                report_result.int_fileschecked += report_file.int_fileschecked
                # Count files that had violations.
                if report_file.list_violations:
                    # Increment the count of files with violations.
                    report_result.int_fileswithviolations += 1
                # Transfer all violations from the file report.
                for violation_item in report_file.list_violations:
                    # Record each violation from this file in the aggregate report.
                    report_result.record(violation_item)
        # Stop after the top-level directory if recursive is disabled.
        if not bool_recursive:
            # Exit the directory walk loop when recursive mode is off.
            break
    # Return the aggregated report.
    return report_result


def run(list_paths: List[str], bool_recursive: bool = True) -> Report:
    """Run checkers on a list of file and directory paths, returning an aggregated Report."""
    # Initialize an empty aggregated report.
    report_result = Report()
    # Process each path in the input list.
    for string_path in list_paths:
        # Analyze individual files directly.
        if os.path.isfile(string_path):
            # Run all checkers on the single file.
            report_file = analyze_file(string_path)
            # Accumulate file count.
            report_result.int_fileschecked += report_file.int_fileschecked
            # Count files with violations.
            if report_file.list_violations:
                # Increment the files-with-violations counter.
                report_result.int_fileswithviolations += 1
            # Transfer violations from the file report.
            for violation_item in report_file.list_violations:
                # Record each violation in the aggregate report.
                report_result.record(violation_item)
        # Analyze directories by walking the tree.
        elif os.path.isdir(string_path):
            # Run all checkers on the directory.
            report_directory = analyze_directory(string_path, bool_recursive=bool_recursive)
            # Accumulate file counts from the directory analysis.
            report_result.int_fileschecked += report_directory.int_fileschecked
            # Accumulate violation file counts.
            report_result.int_fileswithviolations += report_directory.int_fileswithviolations
            # Transfer all violations from the directory analysis.
            for violation_item in report_directory.list_violations:
                # Record each violation from the directory in the aggregate report.
                report_result.record(violation_item)
    # Return the final aggregated report.
    return report_result
