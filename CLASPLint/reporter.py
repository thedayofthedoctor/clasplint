# Define the Violation data class for storing a single CLASP 3.0 rule violation.

from dataclasses import dataclass, field
from typing import List


@dataclass
class Violation:
    """Store a single CLASP 3.0 violation found in source code."""
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


@dataclass
class Report:
    """Aggregate lint report for one or more analyzed files."""
    # Collect all violations found during the analysis run.
    list_violations: List[Violation] = field(default_factory=list)
    # Track the total number of files checked.
    int_fileschecked: int = 0
    # Track the number of files that contained at least one violation.
    int_fileswithviolations: int = 0

    def record(self, violation: Violation) -> None:
        """Append a violation to the report."""
        # Add the violation to the internal violations list.
        self.list_violations.append(violation)

    def summary(self) -> str:
        """Return a human-readable summary string of the analysis results."""
        # Return a clean summary when no violations were found.
        if not self.list_violations:
            # Build and return a clean summary message with file count.
            return (
                f"CLASPLint: {self.int_fileschecked} file(s) checked. "
                f"No CLASP 3.0 violations found."
            )
        # Build a dictionary counting violations by category.
        dict_categorycounts: dict = {}
        # Iterate over all violations to aggregate category counts.
        for violation_item in self.list_violations:
            # Increment the count for the violation's category.
            dict_categorycounts[violation_item.string_category] = (
                dict_categorycounts.get(violation_item.string_category, 0) + 1
            )
        # Build the summary header with overall violation and file counts.
        list_parts = [
            f"CLASPLint: {len(self.list_violations)} violation(s) in "
            f"{self.int_fileswithviolations} of {self.int_fileschecked} file(s)."
        ]
        # Append per-category counts sorted alphabetically.
        for category_name, count_value in sorted(dict_categorycounts.items()):
            list_parts.append(f"  {category_name}: {count_value}")
        # Join all summary parts with newlines and return.
        return "\n".join(list_parts)

    def format_violations(self) -> str:
        """Format all violations for terminal output."""
        # Initialize a list to collect formatted violation lines.
        list_lines = []
        # Iterate over each violation to build formatted output.
        for violation_item in self.list_violations:
            # Build the location string in filepath:linenumber format.
            string_location = f"{violation_item.string_filepath}:{violation_item.int_linenumber}"
            # Format the violation with location, category tag, and message.
            list_lines.append(
                f"  {string_location}  [{violation_item.string_category}] "
                f"{violation_item.string_message}"
            )
            # Append the source line if available for context.
            if violation_item.string_sourceline:
                list_lines.append(
                    f"    -> {violation_item.string_sourceline.strip()}"
                )
        # Join all formatted lines with newlines and return.
        return "\n".join(list_lines)

    @property
    def has_violations(self) -> bool:
        """Return True if any violations were found in the report."""
        # Check whether the violations list is non-empty.
        return len(self.list_violations) > 0
