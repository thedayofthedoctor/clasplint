# Provide the CLASPLint command-line interface entry point.

import argparse
import sys
import os

from .runner import run
from . import __version__


def _init_build_parser_function_() -> argparse.ArgumentParser:
    """Construct the argument parser for the CLASPLint CLI."""
    # Create the top-level argument parser with a description.
    parser_result = argparse.ArgumentParser(
        prog="CLASPLint",
        description="CLASP 3.0 / PEP 2606 static analysis tool. "
                    "Checks variable, dict key, function, class naming "
                    "and comment/log conventions.",
    )
    # Accept one or more file or directory paths as positional arguments.
    parser_result.add_argument(
        "paths", nargs="*", default=["."],
        help="Python files or directories to check (default: current directory).",
    )
    # Provide a --version flag to display the tool version.
    parser_result.add_argument(
        "--version", action="version",
        version=f"CLASPLint {__version__}",
    )
    # Provide a flag to disable recursive directory traversal.
    parser_result.add_argument(
        "--no-recursive", action="store_true",
        help="Do not recursively check subdirectories.",
    )
    # Provide a quiet mode that suppresses per-violation output.
    parser_result.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress individual violation output; show only summary.",
    )
    # Provide a category filter to report only specific violation types.
    parser_result.add_argument(
        "--category", "-c",
        choices=["variable", "dict_key", "function", "comment", "log"],
        help="Only report violations of a specific category.",
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
            v for v in report_result.list_violations
            # Keep only violations matching the requested category filter.
            if v.string_category == args.category
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
