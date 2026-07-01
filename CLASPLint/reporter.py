# -*- coding: utf-8 -*-
"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.reporter -- violation data classes and aggregate report for CLASP 3.1.1 analysis.

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

from dataclasses import dataclass, field
from typing import List


# Mark the Violation class as a data class for automatic __init__ generation.
@dataclass
class Violation:
    """
    Immutable data container for a single CLASP 3.1.1 naming or style violation.

    Public methods:
        (This is a pure data class with no methods.)

    Private methods:
        (This is a pure data class with no private methods.)
    """
    # Store the file path where the violation was detected.
    string_filepath: str
    # Store the line number where the violation occurred.
    int_linenumber: int
    # Store the violation category: variable, dict_key, function, comment, or log.
    string_category: str
    # Store the human-readable violation message.
    string_message: str
    # Store the source code line that triggered the violation.
    string_sourceline: str = ""


# Mark the Report class as a data class for automatic field generation.
@dataclass
class Report:
    """
    Aggregate lint report collecting violations across one or more analyzed files.

    Public methods:
        record -- Append a single violation to the report.
        summary -- Return a human-readable summary string with per-category counts.
        format_violations -- Format all violations as a multi-line terminal display string.
        has_violations -- Property returning True when the report contains violations.

    Private methods:
        (This class has no private methods.)
    """
    # Collect all violations found during the analysis run.
    list_violations: List[Violation] = field(default_factory=list)
    # Track the total number of files checked.
    int_fileschecked: int = 0
    # Track the number of files that contained at least one violation.
    int_fileswithviolations: int = 0

    def record(self, violation: Violation) -> None:
        """
        Append a violation to the report.

        This method stores the given violation in the internal list so that it can
        later be counted, summarized, and formatted for terminal output. It performs
        no validation on the violation object itself.

        :param violation: The Violation instance to add to the internal violations list.
        :type violation: Violation
        """
        # Add the violation to the internal violations list.
        self.list_violations.append(violation)

    def summary(self) -> str:
        """
        Return a human-readable summary string of the analysis results.

        This method aggregates all recorded violations by category, producing a
        header line with total counts and per-category breakdowns sorted
        alphabetically. When no violations exist, it returns a clean confirmation
        message instead.

        :return: A formatted summary with violation counts by category, or a clean message.
        :rtype: str
        """
        # Return a clean summary when no violations were found.
        if not self.list_violations:
            # Build and return a clean summary message with file count.
            return (
                # Format the file count into the summary message.
                f"CLASPLint: {self.int_fileschecked} file(s) checked. "
                # Append the no-violations confirmation message.
                f"No CLASP 3.1.1 violations found."
            # Close the implicit string concatenation tuple.
            )
        # Build a dictionary counting violations by category.
        dict_categorycounts: dict = {}
        # Iterate over all violations to aggregate category counts.
        for violation_item in self.list_violations:
            # Increment the count for the violation's category.
            dict_categorycounts[violation_item.string_category] = (
                # Retrieve the current count or default to zero, then add one.
                dict_categorycounts.get(violation_item.string_category, 0) + 1
            # Close the assignment value for this category count update.
            )
        # Build the summary header with overall violation and file counts.
        list_parts = [
            # Format the total violation count and file count into a header.
            f"CLASPLint: {len(self.list_violations)} violation(s) in "
            # Append the files-with-violations and files-checked counts.
            f"{self.int_fileswithviolations} of {self.int_fileschecked} file(s)."
        # Close the initial summary header list.
        ]
        # Append per-category counts sorted alphabetically.
        for category_name, count_value in sorted(dict_categorycounts.items()):
            # Format and append the per-category count to the summary list.
            list_parts.append(f"  {category_name}: {count_value}")
        # Join all summary parts with newlines and return.
        return "\n".join(list_parts)

    def format_violations(self) -> str:
        """
        Format all violations for terminal output.

        This method iterates over every recorded violation and produces a human-readable
        multi-line string with file location, category tag, and message. When a source
        line snippet is available it is included as contextual detail beneath each entry.

        :return: A multi-line string with each violation formatted for display.
        :rtype: str
        """
        # Initialize a list to collect formatted violation lines.
        list_lines = []
        # Iterate over each violation to build formatted output.
        for violation_item in self.list_violations:
            # Build the location string in filepath:linenumber format.
            string_location = f"{violation_item.string_filepath}:{violation_item.int_linenumber}"
            # Format the violation with location, category tag, and message.
            list_lines.append(
                # Build the location string with category tag prefix.
                f"  {string_location}  [{violation_item.string_category}] "
                # Append the human-readable violation message.
                f"{violation_item.string_message}"
            # Close the append call for the formatted violation line.
            )
            # Append the source line if available for context.
            if violation_item.string_sourceline:
                # Append the source line with an arrow prefix for visual context.
                list_lines.append(
                    # Format the source line with leading whitespace stripped.
                    f"    -> {violation_item.string_sourceline.strip()}"
                # Close the append call for the source context line.
                )
        # Join all formatted lines with newlines and return.
        return "\n".join(list_lines)

    # Expose has_violations as a computed property for convenient boolean checks.
    @property
    def has_violations(self) -> bool:
        """
        Return True if any violations were found in the report.

        This property inspects the internal violations list and returns a boolean
        indicating whether the report contains at least one violation. It is intended
        for convenient truthiness checks in calling code.

        :return: True when the internal violations list is non-empty, False otherwise.
        :rtype: bool
        """
        # Gate conditional display logic so callers only render output when violations exist.
        return len(self.list_violations) > 0
