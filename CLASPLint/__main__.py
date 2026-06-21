"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.__main__ — command-line entry point for the CLASP 3.0 static analysis tool.

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

import argparse
import sys
import os

from .runner import run
from . import __version__


def _init_build_parser_function_() -> argparse.ArgumentParser:
    """Construct the argument parser for the CLASPLint CLI."""
    # Create the top-level argument parser with a description.
    parser_result = argparse.ArgumentParser(
        # Set the program name displayed in help text.
        prog="CLASPLint",
        # Provide a description of what the tool does.
        description="CLASP 3.0 / PEP 2606 static analysis tool. "
                    # Continue the description across multiple lines for readability.
                    "Checks variable, dict key, function, class naming "
                    # Complete the tool description with comment and log conventions.
                    "and comment/log conventions.",
    # Close the ArgumentParser constructor call.
    )
    # Accept one or more file or directory paths as positional arguments.
    parser_result.add_argument(
        # Accept zero or more path strings as positional arguments.
        "paths", nargs="*", default=["."],
        # Provide the help text for the paths argument.
        help="Python files or directories to check (default: current directory).",
    # Close the first add_argument call.
    )
    # Provide a --version flag to display the tool version.
    parser_result.add_argument(
        # Use the version action to print the version string and exit.
        "--version", action="version",
        # Construct the version message from the package version.
        version=f"CLASPLint {__version__}",
    # Close the second add_argument call.
    )
    # Provide a flag to disable recursive directory traversal.
    parser_result.add_argument(
        # Store True when --no-recursive is passed on the command line.
        "--no-recursive", action="store_true",
        # Provide the help text for the no-recursive flag.
        help="Do not recursively check subdirectories.",
    # Close the third add_argument call.
    )
    # Provide a quiet mode that suppresses per-violation output.
    parser_result.add_argument(
        # Support both --quiet and -q flags for convenience.
        "--quiet", "-q", action="store_true",
        # Provide the help text for the quiet flag.
        help="Suppress individual violation output; show only summary.",
    # Close the fourth add_argument call.
    )
    # Provide a category filter to report only specific violation types.
    parser_result.add_argument(
        # Accept --category or -c with a choice of violation types.
        "--category", "-c",
        # Restrict the value to the five supported violation categories.
        choices=["variable", "dict_key", "function", "comment", "log", "docstring"],
        # Provide the help text for the category filter.
        help="Only report violations of a specific category.",
    # Close the fifth add_argument call.
    )
    # Return the fully configured argument parser.
    return parser_result


def main(argv: list = None) -> int:
    """Execute the CLASPLint analysis and return an exit code (0 = clean, 1 = violations)."""
    # Build and parse command-line arguments.
    parser = _init_build_parser_function_()
    # Parse the provided arguments or default to sys.argv.
    args = parser.parse_args(argv)
    # Resolve all input paths to absolute paths for consistent processing.
    list_resolved = []
    # Iterate over each provided path argument.
    for string_path in args.paths:
        # Convert the path to an absolute path.
        string_absolute = os.path.abspath(string_path)
        # Only include paths that exist on the filesystem.
        if os.path.exists(string_absolute):
            # Add the resolved absolute path to the list.
            list_resolved.append(string_absolute)
    # Report an error if no valid paths were found.
    if not list_resolved:
        # Print an error message to stderr.
        print("CLASPLint: No valid Python files or directories found.", file=sys.stderr)
        # Return exit code 2 for usage errors.
        return 2
    # Determine whether to recurse into subdirectories.
    bool_recursive = not args.no_recursive
    # Run all checkers on the resolved paths.
    report_result = run(list_resolved, bool_recursive=bool_recursive)
    # Apply category filter if one was specified.
    if args.category:
        # Filter violations to only the requested category.
        report_result.list_violations = [
            # Iterate over each violation to check against the filter.
            v for v in report_result.list_violations
            # Keep only violations matching the requested category filter.
            if v.string_category == args.category
        # Close the filtered list comprehension.
        ]
    # Print the summary line to stdout.
    print(report_result.summary())
    # Print individual violations unless quiet mode is active.
    if report_result.list_violations and not args.quiet:
        # Add a blank line before the violation listing.
        print()
        # Print the formatted violation details.
        print(report_result.format_violations())
    # Return exit code 1 if violations were found, 0 otherwise.
    return 1 if report_result.has_violations else 0


# Execute the main function when the module is run directly.
if __name__ == "__main__":
    # Exit with the code returned by main().
    sys.exit(main())
