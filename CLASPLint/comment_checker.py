# -*- coding: utf-8 -*-
"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.comment_checker -- Validates every code line has a preceding CLASP 3.1.1 comment.

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
import io
import re
import tokenize
from typing import List, Set, cast

from .reporter import Violation

# Keywords that start lines are exempt from comments since they are structural declarations.
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

# Define weak comment starter patterns that merely restate code rather than explain intent.
patterns_weakcomment = (
    # Detect "Check if ..." and "Check whether ..." patterns that restate conditions.
    r'^Check\s+if\b',
    # Detect "Check whether ..." variant.
    r'^Check\s+whether\b',
# Close the weak comment pattern tuple.
)

# Compile the encoding declaration regex for detecting coding declarations.
regex_encoding = re.compile(
    # Match the standard PEP 263 encoding declaration format.
    r'^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)',
# Close the regex compilation call.
)


def _tokenize_source(string_source: str) -> List[tokenize.TokenInfo]:
    """Tokenize source code and return the list of tokens."""
    # Generate tokens from the source string using a StringIO buffer.
    return list(tokenize.generate_tokens(io.StringIO(string_source).readline))


class CommentChecker:
    """
    Validates that every code line has a preceding comment in CLASP 3.1.1 format,
    and the file header contains the required encoding declaration.

    Public methods:
        run -- Executes all comment-related checks in sequence.

    Private methods:
        _init_check_encoding_function_ -- Verifies the file has a PEP 263 encoding declaration.
        _init_line_comments_function_ -- Verifies every code line has a prior CLASP 3.1.1 comment.
        _init_comment_format_function_ -- Validates comment as capitalized sentence with period.
        _init_chk_weak_comm_function_ -- Detects comments that restate code, not explain intent.
        _init_scan_comm_lang_function_ -- Verifies comment text is written in English.
        _init_chk_sym_comm_function_ -- Detects comments on lines where comments are forbidden.
        _init_docstring_line_function_ -- Determines if a line number falls within a docstring.
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
        Run all comment format, presence, encoding, language, and quality checks.

        Executes the encoding declaration check, line-comment presence check, comment
        format validation, weak comment detection, and comment language verification
        in sequence, populating the internal violations list with any issues found.
        """
        # Verify that the file header contains a PEP 263 encoding declaration.
        self._init_check_encoding_function_()
        # Check that every code line requiring a comment has one.
        self._init_line_comments_function_()
        # Check that every comment follows the required format.
        self._init_comment_format_function_()
        # Detect weak comments that merely restate code rather than explain intent.
        self._init_chk_weak_comm_function_()
        # Verify that comment text is written in English.
        self._init_scan_comm_lang_function_()
        # Detect comments placed on pure-symbol lines where comments are forbidden.
        self._init_chk_sym_comm_function_()

    def _init_line_comments_function_(self) -> None:
        """
        Verify that every physical code line has a preceding comment per CLASP 3.1.1.

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
            # Skip lines that contain no letters (pure symbol lines).
            if not re.search(r'[a-zA-Z]', string_linetext):
                # Exit the loop iteration for pure symbol lines exempt from comment requirement.
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
        CLASP 3.1.1 comment format: each comment must be a self-contained sentence
        starting with '# ', followed by a capital letter, and ending with a period.
        Multi-line comment blocks are prohibited; each comment line stands alone.
        """
        # Attempt to tokenize the source; skip if tokenization fails.
        try:
            # Tokenize the full source code for comment format checking.
            list_tokens = _tokenize_source(self.string_source)
        # Return early if the source cannot be tokenized.
        except tokenize.TokenError:
            # Exit the method early when tokenization fails.
            return
        # Build the set of comment line numbers for block detection.
        set_commentlinenos = set()
        # First pass: collect all valid comment line numbers.
        for token_item in list_tokens:
            # Skip non-comment tokens.
            if token_item.type != tokenize.COMMENT:
                # Proceed to the next token.
                continue
            # Get the raw comment text.
            string_comment = token_item.string
            # Skip comments missing the required '# ' prefix.
            if not string_comment.startswith("# "):
                # Exclude malformed comments from block detection.
                continue
            # Extract the content after '# '.
            string_content = string_comment[2:].strip()
            # Skip empty and special marker comments from block detection.
            if not string_content:
                # Exclude empty placeholder comments.
                continue
            # Skip special markers from block detection.
            if (string_content.startswith("!") or string_content.startswith("type:") or
                    # Filter noqa and encoding marker comments.
                    string_content.startswith("noqa") or string_content.startswith("-*-") or
                    # Filter coding declaration comments.
                    string_content.startswith("coding")):
                # Exclude special marker comments.
                continue
            # Record this line as part of a comment block.
            set_commentlinenos.add(token_item.start[0])
        # Second pass: check each comment for format compliance.
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
                    ),
                    # Supply the source line for contextual display.
                    string_sourceline=self.list_sourcelines[token_item.start[0] - 1],
                ))
                # Skip further checks on malformed comments.
                continue
            # Extract the content after '# '.
            string_content = string_comment[2:].strip()
            # Skip empty comments as they are permitted placeholder comments.
            if not string_content:
                # Proceed to the next token for empty comment content.
                continue
            # Skip special markers like shebang, type: ignore, noqa, and encoding declarations.
            if (string_content.startswith("!") or string_content.startswith("type:") or
                    # Include encoding declaration patterns in the special marker check.
                    string_content.startswith("noqa") or string_content.startswith("-*-") or
                    # Accept the standard coding declaration format as a special marker.
                    string_content.startswith("coding")):
                # Proceed to the next token for special marker comments.
                continue
            # Detect multi-line comment blocks: each comment must be self-contained.
            int_lineno = token_item.start[0]
            # Flag a comment that continues from the previous comment line.
            if (int_lineno - 1) in set_commentlinenos:
                # Record a violation for multi-line comment continuation.
                self.list_violations.append(Violation(
                    # Supply the file path where the continuation comment was detected.
                    string_filepath=self.string_filepath,
                    # Supply the line number of the continuation comment.
                    int_linenumber=int_lineno,
                    # Supply the comment violation category identifier.
                    string_category="comment",
                    # Build the violation message about the multi-line comment.
                    string_message=(
                        # Describe the single-line comment requirement.
                        f"Comment must be a single self-contained line. "
                        # Indicate that this line continues a prior comment.
                        f"Multi-line comment blocks are not permitted."
                    ),
                    # Supply the source line for contextual display.
                    string_sourceline=self.list_sourcelines[int_lineno - 1],
                ))
            # Check that the comment text starts with a capital letter.
            if string_content[0].islower():
                # Record a violation for lowercase start.
                self.list_violations.append(Violation(
                    # Supply the file path where the malformed comment was detected.
                    string_filepath=self.string_filepath,
                    # Supply the line number of the malformed comment.
                    int_linenumber=int_lineno,
                    # Supply the comment violation category identifier.
                    string_category="comment",
                    # Build the violation message describing the format issue.
                    string_message=(
                        # Describe the required capitalization rule.
                        f"Comment text must start with a capital letter. "
                        # Show the first 30 characters of the malformed content.
                        f"Found: '{string_content[:30]}...'"
                    ),
                    # Supply the source line for contextual display.
                    string_sourceline=self.list_sourcelines[int_lineno - 1],
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
                        int_linenumber=int_lineno,
                        # Supply the comment violation category identifier.
                        string_category="comment",
                        # Build the violation message describing the format issue.
                        string_message=(
                            # Describe the required trailing punctuation.
                            f"Comment must end with a period. "
                            # Show the first 40 characters of the malformed content.
                            f"Found: '{string_content[:40]}'"
                        ),
                        # Supply the source line for contextual display.
                        string_sourceline=self.list_sourcelines[int_lineno - 1],
                    ))

    def _init_chk_sym_comm_function_(self) -> None:
        """
        Detect comments placed on pure-symbol lines where comments are forbidden.

        Scans all comment tokens and checks whether the source line containing the
        comment consists solely of non-letter characters. Per CLASP 3.1.1 rule 12,
        pure-symbol lines must not carry comments.
        """
        # Attempt to tokenize the source; skip if tokenization fails.
        try:
            # Tokenize the full source code for symbol-line comment detection.
            list_tokens = _tokenize_source(self.string_source)
        # Return early if the source cannot be tokenized.
        except tokenize.TokenError:
            # Exit the method early when tokenization fails.
            return
        # Inspect each comment token for placement on pure-symbol lines.
        for token_item in list_tokens:
            # Skip non-comment tokens.
            if token_item.type != tokenize.COMMENT:
                # Proceed to the next token in the loop.
                continue
            # Get the line number of the comment token.
            int_lineno = token_item.start[0]
            # Retrieve the full source line at this line number.
            if int_lineno > len(self.list_sourcelines):
                # Skip out-of-bounds line numbers.
                continue
            # Get the raw text of the commented line.
            string_linetext = self.list_sourcelines[int_lineno - 1]
            # Extract the portion of the line before the comment for symbol checking.
            string_beforecomment = string_linetext.split("#")[0] if "#" in string_linetext else ""
            # A pure-symbol line has non-whitespace content before the comment but no letters.
            string_body = string_beforecomment.strip()
            # Skip pure comment lines where there is no code body before the hash.
            if not string_body:
                # Continue to the next token for lines that are purely comment lines.
                continue
            # Detect pure-symbol lines: non-whitespace content present but no letters.
            if not re.search(r'[a-zA-Z]', string_body):
                # Get the comment text for the violation message.
                string_comment = token_item.string
                # Record a violation for a comment on a pure-symbol line.
                self.list_violations.append(Violation(
                        # Supply the file path where the violation was detected.
                        string_filepath=self.string_filepath,
                        # Supply the line number of the offending comment.
                        int_linenumber=int_lineno,
                        # Supply the comment violation category identifier.
                        string_category="comment",
                        # Build the violation message about the forbidden comment.
                        string_message=(
                            # Describe the prohibition on comments for pure-symbol lines.
                            f"Pure-symbol lines must not carry comments. "
                            # Show the offending comment content.
                            f"Remove or relocate: '{string_comment.strip()[:40]}'"
                        # Close the parenthesized message string.
                        ),
                        # Supply the source line for contextual display.
                        string_sourceline=string_linetext,
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
                        # Narrow the first body statement to an expression node.
                        node_expression = cast(ast.Expr, list_body[0])
                        # Extract the expression value for string-constant verification.
                        node_exprvalue = node_expression.value
                        # Verify the expression value is a string constant.
                        if (isinstance(node_exprvalue, ast.Constant)
                                # Additionally verify the contained value is a string literal.
                                and isinstance(node_exprvalue.value, str)):
                            # Get the starting line of the docstring.
                            int_startline = node_expression.lineno
                            # Get the ending line, defaulting to start line if not set.
                            int_endline = getattr(node_expression, 'end_lineno', int_startline)
                            # Determine if the inspected line is inside a docstring to skip checks.
                            if int_startline <= int_lineno <= int_endline:
                                # The line is part of a docstring.
                                return True
        # The line is not part of any docstring.
        return False

    def _init_check_encoding_function_(self) -> None:
        """
        Verify that the file header contains a PEP 263 encoding declaration.

        Checks the first two lines of the source file for an encoding declaration
        in the format '# -*- coding: utf-8 -*-' or '# coding: utf-8'. The first line
        is skipped if it contains a shebang.
        """
        # Split the source into lines for header inspection.
        list_lines = self.list_sourcelines
        # Return early for empty files.
        if not list_lines:
            # Exit early for empty source files.
            return
        # Start checking from the first line.
        int_startindex = 0
        # Skip the first line if it is a shebang.
        if list_lines[0].strip().startswith("#!"):
            # Move to the second line when a shebang is present.
            int_startindex = 1
        # Determine the search range for the encoding declaration.
        int_endindex = min(int_startindex + 2, len(list_lines))
        # Track whether an encoding declaration was found.
        bool_hasencoding = False
        # Search for the encoding declaration in the first two lines.
        for int_index in range(int_startindex, int_endindex):
            # Attempt to match the encoding declaration pattern.
            if regex_encoding.match(list_lines[int_index]):
                # Mark that the encoding declaration was found.
                bool_hasencoding = True
                # Exit the search loop once found.
                break
        # Report a violation if no encoding declaration was found.
        if not bool_hasencoding:
            # Record a missing encoding declaration violation.
            self.list_violations.append(Violation(
                # Supply the file path where the violation was detected.
                string_filepath=self.string_filepath,
                # Report the violation at line 1 or 2 depending on shebang presence.
                int_linenumber=int_startindex + 1,
                # Supply the comment violation category identifier.
                string_category="comment",
                # Build the violation message about the missing encoding declaration.
                string_message=(
                    # Describe the required encoding declaration format.
                    "File is missing a PEP 263 encoding declaration. "
                    # Specify the expected format.
                    "Add '# -*- coding: utf-8 -*-' after the shebang or at the top of the file."
                # Close the parenthesized message string.
                ),
                # Supply the source line for contextual display.
                string_sourceline=(
                    # Provide the source line text or an empty fallback when index is out of range.
                    list_lines[int_startindex] if int_startindex < len(list_lines) else ""),
            # Close the Violation data class instantiation.
            ))

    def _init_chk_weak_comm_function_(self) -> None:
        """
        Detect weak comments that merely restate code rather than explain intent.

        Scans all comment tokens for patterns like 'Check if ...' or 'Check whether ...'
        that only paraphrase the code condition instead of providing meaningful context.
        """
        # Compile the weak comment patterns into regex objects for matching.
        list_weakpatterns = [re.compile(p, re.IGNORECASE) for p in patterns_weakcomment]
        # Attempt to tokenize the source; skip if tokenization fails.
        try:
            # Tokenize the full source code for weak comment detection.
            list_tokens = _tokenize_source(self.string_source)
        # Return early if the source cannot be tokenized.
        except tokenize.TokenError:
            # Exit the method early when tokenization fails.
            return
        # Inspect each comment token for weak patterns.
        for token_item in list_tokens:
            # Skip non-comment tokens.
            if token_item.type != tokenize.COMMENT:
                # Proceed to the next token in the loop.
                continue
            # Get the raw comment text including the leading '#'.
            string_comment = token_item.string
            # Skip comments that do not start with '# ' for weak check.
            if not string_comment.startswith("# "):
                # Proceed to the next token for malformed comments.
                continue
            # Extract the content after '# '.
            string_content = string_comment[2:].strip()
            # Skip empty comment content.
            if not string_content:
                # Proceed to the next token for empty comments.
                continue
            # Check each weak comment pattern against the comment content.
            for regex_pattern in list_weakpatterns:
                # Detect a match of the weak comment pattern.
                if regex_pattern.match(string_content):
                    # Record a violation for the weak comment.
                    self.list_violations.append(Violation(
                        # Supply the file path where the weak comment was detected.
                        string_filepath=self.string_filepath,
                        # Supply the line number of the weak comment.
                        int_linenumber=token_item.start[0],
                        # Supply the comment violation category identifier.
                        string_category="comment",
                        # Build the violation message describing the weak comment issue.
                        string_message=(
                            # Describe the problem with weak comment patterns.
                            f"Weak comment: '{string_content[:50]}...' merely restates code. "
                            # Provide guidance for writing better comments.
                            f"Comments must explain intent, not paraphrase conditions."
                        # Close the parenthesized message string.
                        ),
                        # Supply the source line for contextual display.
                        string_sourceline=self.list_sourcelines[token_item.start[0] - 1],
                    # Close the Violation data class instantiation.
                    ))
                    # Stop checking other patterns once a match is found.
                    break

    def _init_scan_comm_lang_function_(self) -> None:
        """
        Verify that comment text is written in English.

        Scans all comment tokens and detects non-ASCII characters that suggest
        non-English text. Reports a violation when non-English characters are found.
        """
        # Attempt to tokenize the source; skip if tokenization fails.
        try:
            # Tokenize the full source code for comment language detection.
            list_tokens = _tokenize_source(self.string_source)
        # Return early if the source cannot be tokenized.
        except tokenize.TokenError:
            # Exit the method early when tokenization fails.
            return
        # Inspect each comment token for non-English text.
        for token_item in list_tokens:
            # Skip non-comment tokens.
            if token_item.type != tokenize.COMMENT:
                # Proceed to the next token in the loop.
                continue
            # Get the raw comment text including the leading '#'.
            string_comment = token_item.string
            # Skip comments that do not start with '# '.
            if not string_comment.startswith("# "):
                # Proceed to the next token for malformed comments.
                continue
            # Extract the content after '# '.
            string_content = string_comment[2:].strip()
            # Skip empty comment content.
            if not string_content:
                # Proceed to the next token for empty comments.
                continue
            # Skip special marker comments that use fixed-format non-English patterns.
            if (string_content.startswith("!") or string_content.startswith("type:") or
                # Include encoding declaration patterns in the non-English exemption.
                string_content.startswith("noqa") or string_content.startswith("-*-") or
                # Accept the standard coding declaration format as exempt.
                string_content.startswith("coding")):
                # Proceed to the next token for special marker comments.
                continue
            # Detect non-ASCII characters indicating non-English text.
            bool_hasnonenglish = False
            # Iterate over each character in the comment content.
            for char_item in string_content:
                # Check for characters outside the ASCII range.
                if ord(char_item) > 127:
                    # Mark that non-English characters were detected.
                    bool_hasnonenglish = True
                    # Exit the character loop once non-English is found.
                    break
            # Report a violation when non-English characters are found in a comment.
            if bool_hasnonenglish:
                # Record a violation for non-English comment text.
                self.list_violations.append(Violation(
                    # Supply the file path where the non-English comment was detected.
                    string_filepath=self.string_filepath,
                    # Supply the line number of the non-English comment.
                    int_linenumber=token_item.start[0],
                    # Supply the comment violation category identifier.
                    string_category="comment",
                    # Build the violation message about non-English comment text.
                    string_message=(
                        # Describe the language requirement for comments.
                        f"Comment must be written in English. "
                        # Show the first portion of the non-English comment.
                        f"Non-ASCII characters found in: '{string_content[:40]}...'"
                    # Close the parenthesized message string.
                    ),
                    # Supply the source line for contextual display.
                    string_sourceline=self.list_sourcelines[token_item.start[0] - 1],
                # Close the Violation data class instantiation.
                ))
