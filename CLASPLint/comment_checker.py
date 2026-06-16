# Check that every code line has a proper CLASP 3.0 formatted comment.

import ast
import io
import tokenize
from typing import List, Set

from .reporter import Violation

# Define control flow and operation keywords that require a preceding comment.
keywords_requirecomment = frozenset({
    "if", "elif", "else", "for", "while", "try", "except",
    "finally", "with", "return", "raise", "continue", "break",
    "pass",
})


def _tokenize_source(string_source: str) -> List[tokenize.TokenInfo]:
    """Tokenize source code and return the list of tokens."""
    # Generate tokens from the source string using a StringIO buffer.
    return list(tokenize.generate_tokens(io.StringIO(string_source).readline))


class CommentChecker:
    """Check that every code line has a proper CLASP 3.0 comment."""

    def __init__(self, string_filepath: str, string_source: str):
        # Store the file path for violation reporting.
        self.string_filepath = string_filepath
        # Store the full source code as a string.
        self.string_source = string_source
        # Split source into lines for per-line access.
        self.list_sourcelines = string_source.splitlines()
        # Collect violations found during checking.
        self.list_violations: List[Violation] = []

    def run(self) -> None:
        """Run all comment format and presence checks."""
        # Check that every code line requiring a comment has one.
        self._init_line_comments_function_()
        # Check that every comment follows the required format.
        self._init_comment_format_function_()

    def _init_line_comments_function_(self) -> None:
        """Verify that every physical code line with a control keyword has a comment."""
        # Attempt to tokenize the source; skip if tokenization fails.
        try:
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
                set_commentlines.add(token_item.start[0])
            # Add single-line string token line numbers to the code set.
            elif token_item.type == tokenize.STRING and token_item.start[0] == token_item.end[0]:
                set_codelines.add(token_item.start[0])
            # Add all other meaningful token line numbers to the code set.
            elif token_item.type not in (
                tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER,
                tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING,
            ):
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
                    bool_hascomment = True
            # Report a violation if no comment was found for a keyword line.
            if not bool_hascomment:
                # Extract the first word of the line to check against required keywords.
                list_words = string_linetext.split()
                # Default to empty string if the line has no words.
                string_firstword = list_words[0] if list_words else ""
                # Strip trailing colon from keywords like "if:" or "else:".
                string_keyword = string_firstword.rstrip(":")
                # Check if this line's keyword requires a comment.
                if string_keyword in keywords_requirecomment:
                    # Record a missing-comment violation for this keyword line.
                    self.list_violations.append(Violation(
                        string_filepath=self.string_filepath,
                        int_linenumber=int_lineno,
                        string_category="comment",
                        string_message=(
                            f"Line {int_lineno} with keyword '{string_keyword}' "
                            f"lacks a required preceding comment."
                        ),
                        string_sourceline=self.list_sourcelines[int_lineno - 1],
                    ))

    def _init_comment_format_function_(self) -> None:
        """Verify that every comment follows the 'Capitalized sentence.' format."""
        # Attempt to tokenize the source; skip if tokenization fails.
        try:
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
                    string_filepath=self.string_filepath,
                    int_linenumber=token_item.start[0],
                    string_category="comment",
                    string_message=(
                        f"Comment must start with '# ' (hash, space). "
                        f"Found: '{string_comment[:20]}...'"
                    ),
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
            # Skip special marker comments like shebang, type: ignore, and noqa.
            if string_content.startswith("!") or string_content.startswith("type:") or string_content.startswith("noqa"):
                # Proceed to the next token for special marker comments.
                continue
            # Check that the comment text starts with a capital letter.
            if string_content[0].islower():
                # Record a violation for lowercase start.
                self.list_violations.append(Violation(
                    string_filepath=self.string_filepath,
                    int_linenumber=token_item.start[0],
                    string_category="comment",
                    string_message=(
                        f"Comment text must start with a capital letter. "
                        f"Found: '{string_content[:30]}...'"
                    ),
                    string_sourceline=self.list_sourcelines[token_item.start[0] - 1],
                ))
            # Check that the comment text ends with a period or other valid punctuation.
            if not string_content.endswith("."):
                # Allow common sentence-ending punctuation alternatives.
                if not any(string_content.endswith(p) for p in (".", "!", "?", ":", ";", ")")):
                    # Record a violation for missing terminal period.
                    self.list_violations.append(Violation(
                        string_filepath=self.string_filepath,
                        int_linenumber=token_item.start[0],
                        string_category="comment",
                        string_message=(
                            f"Comment must end with a period. "
                            f"Found: '{string_content[:40]}'"
                        ),
                        string_sourceline=self.list_sourcelines[token_item.start[0] - 1],
                    ))

    def _init_docstring_line_function_(self, int_lineno: int) -> bool:
        """Determine whether a given line is part of a docstring."""
        # Attempt to parse the source into an AST; skip if parsing fails.
        try:
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
