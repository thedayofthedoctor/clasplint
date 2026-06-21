"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.comment_checker — Validates that every code line has a preceding CLASP 3.0 formatted comment.

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
import io
import tokenize
from typing import List, Set

from .reporter import Violation

# Define line-starting keywords that are exempt from the comment requirement.
# Imports, class definitions, and function definitions are structural declarations.
keywords_exemptfromcomment = frozenset({
    # Include the standard import statement keyword.
    "import",
    # Include the from-import statement keyword.
    "from",
    # Include the class definition keyword.
    "class",
    # Include the function definition keyword.
    "def",
# Close the exempt keywords frozenset literal.
})


def _tokenize_source(string_source: str) -> List[tokenize.TokenInfo]:
    """Tokenize source code and return the list of tokens."""
    # Generate tokens from the source string using a StringIO buffer.
    return list(tokenize.generate_tokens(io.StringIO(string_source).readline))


class CommentChecker:
    """
    Validates that every code line has a preceding comment and that all comments follow the CLASP 3.0 format.

    Public methods:
        run — Executes both the line-comment presence check and the comment format validation in sequence.

    Private methods:
        _init_line_comments_function_ — Verifies that every physical code line has a preceding comment per CLASP 3.0.
        _init_comment_format_function_ — Validates that every comment follows the capitalized sentence format with a trailing period.
        _init_docstring_line_function_ — Determines whether a given line number falls within a docstring expression.
    """

    def __init__(self, string_filepath: str, string_source: str):
        """
        Initialize the comment checker with the file path and full source code.

        Stores the file path for violation reporting, the complete source as a string for
        tokenization, and splits it into lines for per-line access by format checks.

        :param string_filepath: The absolute path to the Python file being checked.
        :type string_filepath: str
        :param string_source: The complete source code of the file as a single string.
        :type string_source: str
        """
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store the full source code as a string.
        self.string_source = string_source
        # Split source into lines for per-line access.
        self.list_sourcelines = string_source.splitlines()
        # Collect violations found during checking.
        self.list_violations: List[Violation] = []

    def run(self) -> None:
        """
        Run all comment format and presence checks.

        Executes both the line-comment presence check and the comment format validation
        in sequence, populating the internal violations list with any issues found.
        """
        # Check that every code line requiring a comment has one.
        self._init_line_comments_function_()
        # Check that every comment follows the required format.
        self._init_comment_format_function_()

    def _init_line_comments_function_(self) -> None:
        """
        Verify that every physical code line has a preceding comment per CLASP 3.0.

        Tokenizes the source code to identify code lines and comment lines, then checks
        that every non-exempt code line has a comment on the same line or the line before.
        Import, class, and function definition lines are exempt from this requirement.
        """
        # Attempt to tokenize the source; skip if tokenization fails.
        try:
            # Tokenize the full source code into a list of token objects.
            list_tokens = _tokenize_source(self.string_source)
        # Return early if the source cannot be tokenized.
        except tokenize.TokenError:
            # Exit the method early when tokenization fails.
            return
        # Build a set of line numbers containing code tokens.
        set_codelines: Set[int] = set()
        # Build a set of line numbers containing comment tokens.
        set_commentlines: Set[int] = set()
        # Classify each token to identify code lines and comment lines.
        for token_item in list_tokens:
            # Add comment token line numbers to the comment set.
            if token_item.type == tokenize.COMMENT:
                # Record the line number of this comment token.
                set_commentlines.add(token_item.start[0])
            # Add single-line string token line numbers to the code set.
            elif token_item.type == tokenize.STRING and token_item.start[0] == token_item.end[0]:
                # Record the line number of this single-line string token.
                set_codelines.add(token_item.start[0])
            # Add all other meaningful token line numbers to the code set.
            elif token_item.type not in (
                # Exclude newline token types from the code line set.
                tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER,
                # Exclude indentation token types from the code line set.
                tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING,
            # Close the excluded token type tuple.
            ):
                # Record the line number of this meaningful code token.
                set_codelines.add(token_item.start[0])
        # Check each code line for required comments.
        for int_lineno in sorted(set_codelines):
            # Skip lines beyond the source file length.
            if int_lineno > len(self.list_sourcelines):
                # Exit the loop iteration for out-of-bounds line numbers.
                continue
            # Get the trimmed text of the current line.
            string_linetext = self.list_sourcelines[int_lineno - 1].strip()
            # Skip blank lines as they contain no code to comment.
            if not string_linetext:
                # Exit the loop iteration for blank lines.
                continue
            # Skip comment-only lines as they serve as their own comment.
            if int_lineno in set_commentlines and string_linetext.startswith("#"):
                # Exit the loop iteration for comment-only lines.
                continue
            # Skip lines that are part of a docstring.
            if self._init_docstring_line_function_(int_lineno):
                # Exit the loop iteration for docstring lines.
                continue
            # Determine whether a comment exists on the same line or the previous line.
            bool_hascomment = int_lineno in set_commentlines
            # Check the previous non-blank line as an alternative comment location.
            if not bool_hascomment and int_lineno > 1:
                # Get the trimmed text of the previous line.
                string_previoustext = self.list_sourcelines[int_lineno - 2].strip()
                # Treat a preceding comment line as satisfying the requirement.
                if string_previoustext.startswith("#"):
                    # Mark this line as having a valid preceding comment.
                    bool_hascomment = True
            # Report a violation if no comment was found for this code line.
            if not bool_hascomment:
                # Extract the first word to check against exempt structural keywords.
                list_words = string_linetext.split()
                # Default to empty string if the line has no words.
                string_firstword = list_words[0] if list_words else ""
                # Handle "async def" as a two-word function definition starter.
                if string_firstword == "async" and len(list_words) >= 2:
                    # Extract the actual keyword following the async modifier.
                    string_firstword = list_words[1]
                # Skip import, class, and function definition lines.
                if string_firstword in keywords_exemptfromcomment:
                    # Proceed to the next line without reporting a violation.
                    continue
                # Record a missing-comment violation for this physical code line.
                self.list_violations.append(Violation(
                    # Supply the file path where the violation was detected.
                    string_filepath=self.string_filepath,
                    # Supply the line number of the uncommented code line.
                    int_linenumber=int_lineno,
                    # Supply the comment violation category identifier.
                    string_category="comment",
                    # Build the violation message with the line number.
                    string_message=(
                        # Format the line number into the missing-comment message.
                        f"Line {int_lineno} lacks a required preceding comment."
                    # Close the parenthesized message string.
                    ),
                    # Supply the source line for contextual display.
                    string_sourceline=self.list_sourcelines[int_lineno - 1],
                # Close the Violation data class instantiation.
                ))

    def _init_comment_format_function_(self) -> None:
        """
        Verify that every comment follows the 'Capitalized sentence.' format.

        Tokenizes the source and inspects each comment token for compliance with the
        CLASP 3.0 comment format: the comment must start with '# ' (hash and space),
        the text must begin with a capital letter, and it must end with a period.
        """
        # Attempt to tokenize the source; skip if tokenization fails.
        try:
            # Tokenize the full source code for comment format checking.
            list_tokens = _tokenize_source(self.string_source)
        # Return early if the source cannot be tokenized.
        except tokenize.TokenError:
            # Exit the method early when tokenization fails.
            return
        # Check each comment token for format compliance.
        for token_item in list_tokens:
            # Skip non-comment tokens.
            if token_item.type != tokenize.COMMENT:
                # Proceed to the next token in the loop.
                continue
            # Get the raw comment text including the leading '#'.
            string_comment = token_item.string
            # Check that the comment starts with '# ' (hash followed by space).
            if not string_comment.startswith("# "):
                # Record a violation for missing space after hash.
                self.list_violations.append(Violation(
                    # Supply the file path where the malformed comment was detected.
                    string_filepath=self.string_filepath,
                    # Supply the line number of the malformed comment.
                    int_linenumber=token_item.start[0],
                    # Supply the comment violation category identifier.
                    string_category="comment",
                    # Build the violation message describing the format issue.
                    string_message=(
                        # Describe the required comment format.
                        f"Comment must start with '# ' (hash, space). "
                        # Show the first 20 characters of the malformed comment.
                        f"Found: '{string_comment[:20]}...'"
                    # Close the parenthesized message string.
                    ),
                    # Supply the source line for contextual display.
                    string_sourceline=self.list_sourcelines[token_item.start[0] - 1],
                # Close the Violation data class instantiation.
                ))
                # Skip further checks on malformed comments.
                continue
            # Extract the content after '# '.
            string_content = string_comment[2:].strip()
            # Skip empty comments as they are permitted placeholder comments.
            if not string_content:
                # Proceed to the next token for empty comment content.
                continue
            # Skip special marker comments like shebang, type: ignore, and noqa.
            if string_content.startswith("!") or string_content.startswith("type:") or string_content.startswith("noqa"):
                # Proceed to the next token for special marker comments.
                continue
            # Check that the comment text starts with a capital letter.
            if string_content[0].islower():
                # Record a violation for lowercase start.
                self.list_violations.append(Violation(
                    # Supply the file path where the malformed comment was detected.
                    string_filepath=self.string_filepath,
                    # Supply the line number of the malformed comment.
                    int_linenumber=token_item.start[0],
                    # Supply the comment violation category identifier.
                    string_category="comment",
                    # Build the violation message describing the format issue.
                    string_message=(
                        # Describe the required capitalization rule.
                        f"Comment text must start with a capital letter. "
                        # Show the first 30 characters of the malformed content.
                        f"Found: '{string_content[:30]}...'"
                    # Close the parenthesized message string.
                    ),
                    # Supply the source line for contextual display.
                    string_sourceline=self.list_sourcelines[token_item.start[0] - 1],
                # Close the Violation data class instantiation.
                ))
            # Check that the comment text ends with a period or other valid punctuation.
            if not string_content.endswith("."):
                # Allow common sentence-ending punctuation alternatives.
                if not any(string_content.endswith(p) for p in (".", "!", "?", ":", ";", ")")):
                    # Record a violation for missing terminal period.
                    self.list_violations.append(Violation(
                        # Supply the file path where the malformed comment was detected.
                        string_filepath=self.string_filepath,
                        # Supply the line number of the malformed comment.
                        int_linenumber=token_item.start[0],
                        # Supply the comment violation category identifier.
                        string_category="comment",
                        # Build the violation message describing the format issue.
                        string_message=(
                            # Describe the required trailing punctuation.
                            f"Comment must end with a period. "
                            # Show the first 40 characters of the malformed content.
                            f"Found: '{string_content[:40]}'"
                        # Close the parenthesized message string.
                        ),
                        # Supply the source line for contextual display.
                        string_sourceline=self.list_sourcelines[token_item.start[0] - 1],
                    # Close the Violation data class instantiation.
                    ))

    def _init_docstring_line_function_(self, int_lineno: int) -> bool:
        """
        Determine whether a given line is part of a docstring.

        Parses the source into an AST and walks all nodes to locate docstring expressions.
        For each function, class, and module node with a docstring, checks whether the
        queried line number falls within the docstring's start and end line range.

        :param int_lineno: The 1-based line number to check for docstring membership.
        :type int_lineno: int
        :return: True if the line is within a docstring expression, False otherwise.
        :rtype: bool
        """
        # Attempt to parse the source into an AST; skip if parsing fails.
        try:
            # Parse the source code to locate docstring nodes.
            tree = ast.parse(self.string_source)
        # Return False if the source has syntax errors.
        except SyntaxError:
            # Return False to indicate the line is not part of a docstring.
            return False
        # Walk all AST nodes to find docstring nodes.
        for node in ast.walk(tree):
            # Check function, class, and module nodes for docstrings.
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                # Retrieve the docstring using ast.get_docstring.
                string_docstring = ast.get_docstring(node)
                # Skip nodes without docstrings.
                if string_docstring:
                    # Access the first statement in the body (the docstring expression).
                    list_body = node.body
                    # Verify the body exists and the first statement is an expression.
                    if list_body and isinstance(list_body[0], ast.Expr):
                        # Get the expression node.
                        node_expression = list_body[0]
                        # Verify the expression value is a string constant.
                        if isinstance(node_expression.value, ast.Constant) and isinstance(node_expression.value.value, str):
                            # Get the starting line of the docstring.
                            int_startline = node_expression.lineno
                            # Get the ending line, defaulting to start line if not set.
                            int_endline = node_expression.end_lineno or int_startline
                            # Check whether the queried line falls within the docstring range.
                            if int_startline <= int_lineno <= int_endline:
                                # The line is part of a docstring.
                                return True
        # The line is not part of any docstring.
        return False
