"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.naming_utils — naming validation utilities and lookup tables for CLASP 3.0 rules.

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
import re

# Define the set of well-known acronyms allowed in lowercase form within variable and function names.
acronyms_lowercase = frozenset({
# Include geospatial positioning and data format acronyms.
    "gps", "utm", "xmp", "gdal", "epsg", "xml",
# Include remote sensing band and coordinate system acronyms.
    "rgb", "nir", "ndvi", "gsd", "crs", "wkt",
# Include data serialization and web protocol acronyms.
    "json", "yaml", "html", "http", "url", "api",
# Include the remaining database, image format, and logging level acronyms.
    "sql", "csv", "tif", "tiff", "png", "jpeg", "message_info"
# Close the acronyms_lowercase frozenset literal.
})

# Define the set of well-known acronyms kept in uppercase form for dictionary keys.
acronyms_uppercase = frozenset({
# Include uppercase geospatial and data format acronyms.
    "GPS", "UTM", "XMP", "GDAL", "EPSG", "XML",
# Include uppercase remote sensing and coordinate system acronyms.
    "RGB", "NIR", "NDVI", "GSD", "CRS", "WKT",
# Include uppercase serialization and web protocol acronyms.
    "JSON", "YAML", "HTML", "HTTP", "URL", "API",
# Include uppercase database and image format acronyms.
    "SQL", "CSV", "TIF", "TIFF", "PNG", "JPEG",
# Include uppercase time and identifier acronyms.
    "UTC", "ID",
# Close the acronyms_uppercase frozenset literal.
})

# Map common English abbreviations to their full word equivalents for violation detection.
abbreviations_forbidden = {
# Map the abbreviation "dir" to its full word "directory".
    "dir": "directory",
# Map the abbreviation "idx" to its full word "index".
    "idx": "index",
# Map the abbreviation "seq" to its full word "sequence".
    "seq": "sequence",
# Map the abbreviation "coeff" to its full word "coefficient".
    "coeff": "coefficient",
# Map the abbreviation "mul" to its full word "multiplier".
    "mul": "multiplier",
# Map the abbreviation "cfg" to its full word "configuration".
    "cfg": "configuration",
# Map the abbreviation "conf" to its full word "configuration".
    "conf": "configuration",
# Map the abbreviation "config" to its full word "configuration".
    "config": "configuration",
# Map the abbreviation "init" to its full word "initialize".
    "init": "initialize",
# Map the abbreviation "param" to its full word "parameter".
    "param": "parameter",
# Map the abbreviation "arg" to its full word "argument".
    "arg": "argument",
# Map the abbreviation "attr" to its full word "attribute".
    "attr": "attribute",
# Map the abbreviation "buf" to its full word "buffer".
    "buf": "buffer",
# Map the abbreviation "calc" to its full word "calculate".
    "calc": "calculate",
# Map the abbreviation "coord" to its full word "coordinate".
    "coord": "coordinate",
# Map the abbreviation "dest" to its full word "destination".
    "dest": "destination",
# Map the abbreviation "err" to its full word "error".
    "err": "error",
# Map the abbreviation "exc" to its full word "exception".
    "exc": "exception",
# Map the abbreviation "exec" to its full word "execute".
    "exec": "execute",
# Map the abbreviation "expr" to its full word "expression".
    "expr": "expression",
# Map the abbreviation "fmt" to its full word "format".
    "fmt": "format",
# Map the abbreviation "func" to its full word "function".
    "func": "function",
# Map the abbreviation "info" to its full word "information".
    "info": "information",
# Map the abbreviation "lang" to its full word "language".
    "lang": "language",
# Map the abbreviation "lib" to its full word "library".
    "lib": "library",
# Map the abbreviation "max" to its full word "maximum".
    "max": "maximum",
# Map the abbreviation "min" to its full word "minimum".
    "min": "minimum",
# Map the abbreviation "msg" to its full word "message".
    "msg": "message",
# Map the abbreviation "num" to its full word "number".
    "num": "number",
# Map the abbreviation "obj" to its full word "object".
    "obj": "object",
# Map the abbreviation "pos" to its full word "position".
    "pos": "position",
# Map the abbreviation "prev" to its full word "previous".
    "prev": "previous",
# Map the abbreviation "proc" to its full word "process".
    "proc": "process",
# Map the abbreviation "ref" to its full word "reference".
    "ref": "reference",
# Map the abbreviation "reg" to its full word "register".
    "reg": "register",
# Map the abbreviation "req" to its full word "request".
    "req": "request",
# Map the abbreviation "resp" to its full word "response".
    "resp": "response",
# Map the abbreviation "src" to its full word "source".
    "src": "source",
# Map the abbreviation "std" to its full word "standard".
    "std": "standard",
# Map the abbreviation "str" to its full word "string".
    "str": "string",
# Map the abbreviation "sync" to its full word "synchronize".
    "sync": "synchronize",
# Map the abbreviation "temp" to its full word "temporary".
    "temp": "temporary",
# Map the abbreviation "tmp" to its full word "temporary".
    "tmp": "temporary",
# Map the abbreviation "txt" to its full word "text".
    "txt": "text",
# Map the abbreviation "val" to its full word "value".
    "val": "value",
# Map the abbreviation "var" to its full word "variable".
    "var": "variable",
# Map the abbreviation "ver" to its full word "version".
    "ver": "version",
# Close the abbreviations_forbidden dictionary literal.
}

# Define the set of type prefixes allowed at the start of variable names.
prefixes_validtype = frozenset({
# Include basic container and scalar type prefixes.
    "list", "dict", "string", "bool", "int", "float",
# Include additional container and binary type prefixes.
    "tuple", "set", "bytes", "bytearray", "frozenset",
# Include scientific computing type prefixes.
    "array", "dataframe", "series", "tensor", "ndarray",
# Close the prefixes_validtype frozenset literal.
})

# Define the set of boolean-specific prefixes for variable names.
prefixes_boolean = frozenset({"is", "has"})

# Define the set of vague verbs that trigger a warning in function names.
# "run" and "start" are explicitly permitted as concise public method names per CLASP 3.0.
verbs_vague = frozenset({
# Include general action verbs considered too vague.
    "process", "handle", "manage", "do", "execute",
# Include additional overly broad action verbs.
    "perform", "operate", "work", "apply", "make", "create",
# Include utility and accessor verbs considered too generic.
    "setup", "init", "clean", "check", "get", "set",
# Include CRUD operation verbs considered too generic.
    "update", "delete", "remove", "add",
# Close the verbs_vague frozenset literal.
})

# Define variable names exempt from checking due to Python built-in conventions.
# "node" is exempt as it is the standard AST visitor pattern parameter name.
# Short utility parameter names are exempt as they serve single obvious purposes.
names_exempt = frozenset({
# Include standard instance and class parameter names.
    "self", "cls",
# Include the underscore throwaway variable name.
    "_",
# Include AST visitor and utility parameter names.
    "node", "tree", "name", "key", "target",
# Include command-line and parser-related exempt names.
    "args", "argv", "parser", "violation",
# Close the names_exempt frozenset literal.
})

# Define compound names exempt from abbreviation checking due to domain-specific semantics.
# Log level terms (debug, info, warning, error, critical) are standard Python logging names.
# These are not abbreviations when used as the second group after a descriptive prefix.
compound_exemptions = frozenset({
# Include logging level compound names exempt from abbreviation checking.
    "message_info", "message_debug", "message_warning", "message_error", "message_critical",
# Close the compound_exemptions frozenset literal.
})

# Define the maximum allowed character length for variable and function names.
length_namemax = 30


def is_underscore_single(name: str) -> bool:
    """Return True if the name has exactly one underscore in group1_group2 format."""
    # Return True only if exactly one underscore is present and not at the start.
    return name.count("_") == 1 and not name.startswith("_")


def split_name_groups(name: str) -> list:
    """Split a name by underscore into its component groups."""
    # Split and return the groups separated by underscores.
    return name.split("_")


def is_all_lowercase(name: str) -> bool:
    """Return True if the name contains no uppercase letters."""
    # Compare against the lowercase version to detect uppercase characters.
    return name == name.lower()


def detect_abbreviations(name: str) -> list:
    """Return a list of (abbreviation, full_word) tuples found in name groups."""
    # Skip abbreviation checking for compound names with domain-specific semantics.
    if name in compound_exemptions:
        # Return an empty list for exempt compound names like message_info.
        return []
    # Initialize an empty list to collect abbreviation violations.
    list_violations = []
    # Split the name into underscore-separated groups for per-group checking.
    list_groups = split_name_groups(name)
    # Iterate over each group to detect known abbreviations.
    for group_name in list_groups:
        # Skip the "init" group when it is part of the _init_X_function_ private method prefix.
        if group_name == "init" and name.startswith("_init_"):
            # Proceed to the next group without flagging the init prefix part.
            continue
        # Check if the current group matches a forbidden abbreviation.
        if group_name in abbreviations_forbidden:
            # Append the abbreviation and its full form to the violations list.
            list_violations.append((group_name, abbreviations_forbidden[group_name]))
    # Return the collected list of abbreviation violations.
    return list_violations


def validate_namelength(name: str) -> bool:
    """Return True if the name does not exceed the maximum allowed length."""
    # Compare the name length against the maximum allowed length.
    return len(name) <= length_namemax


def is_pascal_case(name: str) -> bool:
    """Return True if name follows PascalCase: starts with uppercase and has no underscores."""
    # Reject names containing underscores as non-PascalCase.
    if "_" in name:
        # No underscores allowed in valid PascalCase names.
        return False
    # Reject empty strings as invalid.
    if not name:
        # Empty strings are not valid PascalCase identifiers.
        return False
    # Reject names not starting with an uppercase letter.
    if not name[0].isupper():
        # Names must start with an uppercase letter to be PascalCase.
        return False
    # All checks passed; the name is in valid PascalCase.
    return True


def is_snake_case(name: str) -> bool:
    """Return True if name follows snake_case: all lowercase with optional underscores."""
    # Compare the name against its lowercase version to detect uppercase characters.
    if name != name.lower():
        # Uppercase letters detected; the name is not valid snake_case.
        return False
    # No uppercase letters found; the name is in valid snake_case.
    return True


def validate_dictkey_format(key: str) -> list:
    """Check a dictionary key for PascalCase and abbreviation violations.
    Returns a list of violation message strings.
    """
    # Initialize an empty list to collect dict key violations.
    list_violations = []
    # Exempt single lowercase word keys that represent lookup data values.
    # Per CLASP §二.第六, these are not configuration names requiring PascalCase.
    if key == key.lower() and "_" not in key:
        # Return an empty list for lookup-table keys that don't need PascalCase.
        return list_violations
    # Check that the dict key uses PascalCase format.
    if not is_pascal_case(key):
        # Record a violation for non-PascalCase key format.
        list_violations.append(
# Format a dictionary key PascalCase format violation message with the key name.
            f"Dict key '{key}' is not in PascalCase format."
# Close the violation message append call.
        )
    # Split the PascalCase key into individual words for abbreviation checking.
    list_words = re.findall(r'[A-Z][a-z]*|[A-Z]+(?=[A-Z][a-z]|\d|\b)', key)
    # Iterate over each word to detect forbidden abbreviations.
    for word_item in list_words:
        # Convert the word to lowercase for abbreviation lookup.
        string_lower = word_item.lower()
        # Check if the lowercase word is a known forbidden abbreviation.
        if string_lower in abbreviations_forbidden:
            # Record a violation with the abbreviation and its correct full form.
            list_violations.append(
# Format an abbreviation violation message for the dictionary key.
                f"Dict key '{key}' contains abbreviated word '{word_item}' "
# Specify the correct full word to use instead of the abbreviation.
                f"(use '{abbreviations_forbidden[string_lower]}' instead)."
# Close the violation message append call.
            )
    # Return the collected list of dict key violations.
    return list_violations


def is_private_method_format(name: str) -> bool:
    """Check if name follows the _init_X_function_ private method pattern."""
    # Use regex to match the required _init_..._function_ private method format.
    return bool(re.match(r'^_init_[a-z][a-z0-9]*(_[a-z][a-z0-9]*)*_function_$', name))


def validate_variable_name(name: str) -> list:
    """Validate a variable name against CLASP 3.0 rules.
    Returns a list of violation message strings (empty if valid).
    """
    # Initialize an empty list to collect variable name violations.
    list_violations = []
    # Check that the variable name has exactly one underscore.
    if not is_underscore_single(name):
        # Record a violation for missing or excessive underscores.
        list_violations.append(
# Format the underscore count violation message for the variable.
            f"Variable '{name}' must have exactly one underscore in group1_group2 format."
# Close the violation message append call.
        )
        # Return early since further checks depend on correct underscore format.
        return list_violations
    # Check that the variable name contains no uppercase letters.
    if not is_all_lowercase(name):
        # Record a violation for uppercase characters in the name.
        list_violations.append(
# Format the uppercase letters violation message for the variable.
            f"Variable '{name}' contains uppercase letters; must be all lowercase."
# Close the violation message append call.
        )
    # Detect any forbidden abbreviations within the variable name.
    list_abbreviations = detect_abbreviations(name)
    # Iterate over each detected abbreviation to record violations.
    for abbr_item, full_item in list_abbreviations:
        # Record a violation describing the abbreviation and its full form.
        list_violations.append(
# Specify the correct full word to use instead of the abbreviation.
            f"Variable '{name}' contains abbreviation '{abbr_item}' (use '{full_item}' instead)."
# Close the violation message append call.
        )
    # Check that the variable name length does not exceed the maximum.
    if not validate_namelength(name):
        # Record a violation for excessive name length.
        list_violations.append(
# Format the length violation message for the variable.
            f"Variable '{name}' exceeds {length_namemax} characters (length: {len(name)})."
# Close the violation message append call.
        )
    # Return the collected list of variable name violations.
    return list_violations


def validate_function_name(name: str, is_method: bool = False, is_astvisitor: bool = False) -> list:
    """Validate a function or method name against CLASP 3.0 rules.
    Returns a list of violation message strings.
    """
    # Initialize an empty list to collect function name violations.
    list_violations = []
    # Exempt Python dunder methods (__init__, __new__, __str__, etc.) from checking.
    if name.startswith("__") and name.endswith("__"):
        # Return empty violations list for dunder methods.
        return list_violations
    # Exempt AST visitor methods only when the class inherits from ast.NodeVisitor.
    if is_astvisitor and name.startswith("visit_"):
        # Return empty violations list for AST visitor methods in NodeVisitor subclasses.
        return list_violations
    # Check private method format when applicable.
    if is_method and name.startswith("_") and not name.startswith("__"):
        # Validate the _init_..._function_ pattern for private methods.
        if not is_private_method_format(name):
            # Record a violation for incorrect private method format.
            list_violations.append(
# Format the private method format violation message.
                f"Private method '{name}' does not match '_init_X_function_' format."
# Close the violation message append call.
            )
        # Return early for private methods; no further checks apply.
        return list_violations
    # Check that public methods do not start or end with an underscore.
    if is_method and (name.startswith("_") or name.endswith("_")):
        # Record a violation for leading or trailing underscore on public method.
        list_violations.append(
# Format the public method underscore violation message.
            f"Public method '{name}' must not start or end with underscore."
# Close the violation message append call.
        )
    # Check that the function name uses all-lowercase snake_case.
    if not is_snake_case(name):
        # Record a violation for uppercase characters in the function name.
        list_violations.append(
# Format the uppercase letters violation message for the function.
            f"Function '{name}' contains uppercase letters; must be all lowercase."
# Close the violation message append call.
        )
    # Split the function name into underscore-separated groups for abbreviation checking.
    list_groups = split_name_groups(name)
    # Iterate over each group to detect forbidden abbreviations.
    for group_item in list_groups:
        # Skip the "init" group when it is part of the _init_X_function_ private prefix.
        if group_item == "init" and name.startswith("_init_"):
            # Proceed to the next group without flagging the init prefix part.
            continue
        # Check if the current group is a known forbidden abbreviation.
        if group_item in abbreviations_forbidden:
            # Record a violation with the abbreviation and its correct full form.
            list_violations.append(
# Format the abbreviation violation message for the function.
                f"Function '{name}' contains abbreviation '{group_item}' "
# Specify the correct full word to use instead of the abbreviation.
                f"(use '{abbreviations_forbidden[group_item]}' instead)."
# Close the violation message append call.
            )
    # Check that the function name length does not exceed the maximum.
    if not validate_namelength(name):
        # Record a violation for excessive function name length.
        list_violations.append(
# Format the length violation message for the function.
            f"Function '{name}' exceeds {length_namemax} characters (length: {len(name)})."
# Close the violation message append call.
        )
    # Check for vague verbs at the start of the function name.
    string_firstgroup = split_name_groups(name)[0] if "_" in name else name
    # Compare the first group against the set of vague verbs.
    if string_firstgroup in verbs_vague:
        # Record a violation suggesting a more specific verb.
        list_violations.append(
# Format the vague verb violation message for the function.
            f"Function '{name}' starts with vague verb '{string_firstgroup}'; "
# Append the suggestion to use a more specific verb.
            f"use a more specific verb."
# Close the violation message append call.
        )
    # Return the collected list of function name violations.
    return list_violations


def validate_class_name(name: str) -> list:
    """Validate a class name against CLASP 3.0 rules.
    Returns a list of violation message strings.
    """
    # Initialize an empty list to collect class name violations.
    list_violations = []
    # Check that the class name uses PascalCase format.
    if not is_pascal_case(name):
        # Record a violation for non-PascalCase class name.
        list_violations.append(
# Format the PascalCase violation message for the class.
            f"Class '{name}' is not in PascalCase format."
# Close the violation message append call.
        )
    # Split the PascalCase class name into individual words for abbreviation checking.
    list_words = re.findall(r'[A-Z][a-z]*|[A-Z]+(?=[A-Z][a-z]|\d|\b)', name)
    # Iterate over each word to detect forbidden abbreviations.
    for word_item in list_words:
        # Convert the word to lowercase for abbreviation lookup.
        string_lower = word_item.lower()
        # Check if the lowercase word is a known forbidden abbreviation.
        if string_lower in abbreviations_forbidden:
            # Record a violation with the abbreviation and its correct full form.
            list_violations.append(
# Format the abbreviation violation message for the class.
                f"Class '{name}' contains abbreviated word '{word_item}' "
# Specify the correct full word to use instead of the abbreviation.
                f"(use '{abbreviations_forbidden[string_lower]}' instead)."
# Close the violation message append call.
            )
    # Return the collected list of class name violations.
    return list_violations
