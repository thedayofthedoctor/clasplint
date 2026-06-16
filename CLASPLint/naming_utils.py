# Import the regular expression module for pattern matching.
import re

# Define the set of well-known acronyms allowed in lowercase form within variable and function names.
acronyms_lowercase = frozenset({
    "gps", "utm", "xmp", "gdal", "epsg", "xml",
    "rgb", "nir", "ndvi", "gsd", "crs", "wkt",
    "json", "yaml", "html", "http", "url", "api",
    "sql", "csv", "tif", "tiff", "png", "jpeg",
})

# Define the set of well-known acronyms kept in uppercase form for dictionary keys.
acronyms_uppercase = frozenset({
    "GPS", "UTM", "XMP", "GDAL", "EPSG", "XML",
    "RGB", "NIR", "NDVI", "GSD", "CRS", "WKT",
    "JSON", "YAML", "HTML", "HTTP", "URL", "API",
    "SQL", "CSV", "TIF", "TIFF", "PNG", "JPEG",
    "UTC", "ID",
})

# Map common English abbreviations to their full word equivalents for violation detection.
abbreviations_forbidden = {
    "dir": "directory",
    "idx": "index",
    "seq": "sequence",
    "coeff": "coefficient",
    "mul": "multiplier",
    "cfg": "configuration",
    "conf": "configuration",
    "config": "configuration",
    "init": "initialize",
    "param": "parameter",
    "arg": "argument",
    "attr": "attribute",
    "buf": "buffer",
    "calc": "calculate",
    "coord": "coordinate",
    "dest": "destination",
    "err": "error",
    "exc": "exception",
    "exec": "execute",
    "expr": "expression",
    "fmt": "format",
    "func": "function",
    "info": "information",
    "lang": "language",
    "lib": "library",
    "max": "maximum",
    "min": "minimum",
    "msg": "message",
    "num": "number",
    "obj": "object",
    "pos": "position",
    "prev": "previous",
    "proc": "process",
    "ref": "reference",
    "reg": "register",
    "req": "request",
    "resp": "response",
    "src": "source",
    "std": "standard",
    "str": "string",
    "sync": "synchronize",
    "temp": "temporary",
    "tmp": "temporary",
    "txt": "text",
    "val": "value",
    "var": "variable",
    "ver": "version",
}

# Define the set of type prefixes allowed at the start of variable names.
prefixes_validtype = frozenset({
    "list", "dict", "string", "bool", "int", "float",
    "tuple", "set", "bytes", "bytearray", "frozenset",
    "array", "dataframe", "series", "tensor", "ndarray",
})

# Define the set of boolean-specific prefixes for variable names.
prefixes_boolean = frozenset({"is", "has"})

# Define the set of vague verbs that trigger a warning in function names.
# "run" and "start" are explicitly permitted as concise public method names per CLASP 3.0.
verbs_vague = frozenset({
    "process", "handle", "manage", "do", "execute",
    "perform", "operate", "work", "apply", "make", "create",
    "setup", "init", "clean", "check", "get", "set",
    "update", "delete", "remove", "add",
})

# Define variable names exempt from checking due to Python built-in conventions.
# "node" is exempt as it is the standard AST visitor pattern parameter name.
# Short utility parameter names are exempt as they serve single obvious purposes.
names_exempt = frozenset({
    "self", "cls",
    "_",
    "node", "tree", "name", "key", "target",
    "args", "argv", "parser", "violation",
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
            f"Dict key '{key}' is not in PascalCase format."
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
                f"Dict key '{key}' contains abbreviated word '{word_item}' "
                f"(use '{abbreviations_forbidden[string_lower]}' instead)."
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
            f"Variable '{name}' must have exactly one underscore in group1_group2 format."
        )
        # Return early since further checks depend on correct underscore format.
        return list_violations
    # Check that the variable name contains no uppercase letters.
    if not is_all_lowercase(name):
        # Record a violation for uppercase characters in the name.
        list_violations.append(
            f"Variable '{name}' contains uppercase letters; must be all lowercase."
        )
    # Detect any forbidden abbreviations within the variable name.
    list_abbreviations = detect_abbreviations(name)
    # Iterate over each detected abbreviation to record violations.
    for abbr_item, full_item in list_abbreviations:
        # Record a violation describing the abbreviation and its full form.
        list_violations.append(
            f"Variable '{name}' contains abbreviation '{abbr_item}' (use '{full_item}' instead)."
        )
    # Check that the variable name length does not exceed the maximum.
    if not validate_namelength(name):
        # Record a violation for excessive name length.
        list_violations.append(
            f"Variable '{name}' exceeds {length_namemax} characters (length: {len(name)})."
        )
    # Return the collected list of variable name violations.
    return list_violations


def validate_function_name(name: str, is_method: bool = False) -> list:
    """Validate a function or method name against CLASP 3.0 rules.
    Returns a list of violation message strings.
    """
    # Initialize an empty list to collect function name violations.
    list_violations = []
    # Exempt Python dunder methods (__init__, __new__, __str__, etc.) from checking.
    if name.startswith("__") and name.endswith("__"):
        # Return empty violations list for dunder methods.
        return list_violations
    # Exempt AST visitor methods (visit_*) as they are required by Python's ast.NodeVisitor API.
    if name.startswith("visit_"):
        # Return empty violations list for AST visitor methods.
        return list_violations
    # Check private method format when applicable.
    if is_method and name.startswith("_") and not name.startswith("__"):
        # Validate the _init_..._function_ pattern for private methods.
        if not is_private_method_format(name):
            # Record a violation for incorrect private method format.
            list_violations.append(
                f"Private method '{name}' does not match '_init_X_function_' format."
            )
        # Return early for private methods; no further checks apply.
        return list_violations
    # Check that public methods do not start or end with an underscore.
    if is_method and (name.startswith("_") or name.endswith("_")):
        # Record a violation for leading or trailing underscore on public method.
        list_violations.append(
            f"Public method '{name}' must not start or end with underscore."
        )
    # Check that the function name uses all-lowercase snake_case.
    if not is_snake_case(name):
        # Record a violation for uppercase characters in the function name.
        list_violations.append(
            f"Function '{name}' contains uppercase letters; must be all lowercase."
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
                f"Function '{name}' contains abbreviation '{group_item}' "
                f"(use '{abbreviations_forbidden[group_item]}' instead)."
            )
    # Check that the function name length does not exceed the maximum.
    if not validate_namelength(name):
        # Record a violation for excessive function name length.
        list_violations.append(
            f"Function '{name}' exceeds {length_namemax} characters (length: {len(name)})."
        )
    # Check for vague verbs at the start of the function name.
    string_firstgroup = split_name_groups(name)[0] if "_" in name else name
    # Compare the first group against the set of vague verbs.
    if string_firstgroup in verbs_vague:
        # Record a violation suggesting a more specific verb.
        list_violations.append(
            f"Function '{name}' starts with vague verb '{string_firstgroup}'; "
            f"use a more specific verb."
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
            f"Class '{name}' is not in PascalCase format."
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
                f"Class '{name}' contains abbreviated word '{word_item}' "
                f"(use '{abbreviations_forbidden[string_lower]}' instead)."
            )
    # Return the collected list of class name violations.
    return list_violations
