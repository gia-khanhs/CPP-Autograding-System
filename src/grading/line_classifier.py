import re
from typing import Literal

CoarseLabel = Literal["input", "output", "logic"]
FineLabel = Literal[
    "input", "output", "logic",
    "declaration", "structure", "comment", "blank"
]


INPUT_PATTERNS = [
    re.compile(r'\bcin\s*>>'),
    re.compile(r'\bgetline\s*\('),
    re.compile(r'\bscanf\s*\('),
    re.compile(r'\bfscanf\s*\('),
    re.compile(r'\bgetchar\s*\('),
    re.compile(r'\bfgets\s*\('),
    re.compile(r'\bfread\s*\('),
]

OUTPUT_PATTERNS = [
    re.compile(r'\bcout\s*<<'),
    re.compile(r'\bcerr\s*<<'),
    re.compile(r'\bclog\s*<<'),
    re.compile(r'\bprintf\s*\('),
    re.compile(r'\bfprintf\s*\('),
    re.compile(r'\bputs\s*\('),
    re.compile(r'\bputchar\s*\('),
    re.compile(r'\bfwrite\s*\('),
]

COMMENT_PATTERNS = [
    re.compile(r'^\s*//'),
    re.compile(r'^\s*/\*'),
    re.compile(r'^\s*\*'),
    re.compile(r'^\s*\*/'),
]

STRUCTURE_PATTERNS = [
    re.compile(r'^\s*#'),
    re.compile(r'^\s*using\b'),
    re.compile(r'^\s*(class|struct|enum|namespace)\b'),
    re.compile(r'^\s*(public|private|protected)\s*:'),
    re.compile(r'^\s*[{}]\s*$'),
]

DECLARATION_PATTERNS = [
    re.compile(
        r'^\s*(const\s+)?'
        r'(short|int|long|long long|float|double|char|bool|string|auto|void)\b'
    ),
]

CONTROL_PATTERNS = [
    re.compile(r'^\s*if\b'),
    re.compile(r'^\s*else\b'),
    re.compile(r'^\s*for\b'),
    re.compile(r'^\s*while\b'),
    re.compile(r'^\s*switch\b'),
    re.compile(r'^\s*case\b'),
    re.compile(r'^\s*default\b'),
    re.compile(r'^\s*return\b'),
    re.compile(r'^\s*break\b'),
    re.compile(r'^\s*continue\b'),
]

FUNCTION_DEF_PATTERN = re.compile(
    r'^\s*[\w:<>\*&\s]+\b\w+\s*\([^;]*\)\s*(const)?\s*\{?\s*$'
)

ASSIGNMENT_PATTERN = re.compile(r'(?<![=!<>])=(?!=)')
CALL_PATTERN = re.compile(r'\b[A-Za-z_]\w*\s*\(')


def classify_fine_line(line: str) -> FineLabel:
    stripped = line.strip()

    if stripped == "":
        return "blank"

    for pat in COMMENT_PATTERNS:
        if pat.search(line):
            return "comment"

    for pat in STRUCTURE_PATTERNS:
        if pat.search(line):
            return "structure"

    for pat in INPUT_PATTERNS:
        if pat.search(line):
            return "input"

    for pat in OUTPUT_PATTERNS:
        if pat.search(line):
            return "output"

    if FUNCTION_DEF_PATTERN.search(line) and not stripped.endswith(";"):
        return "structure"

    if any(p.search(line) for p in DECLARATION_PATTERNS):
        if "(" not in line or stripped.endswith(";"):
            if not ASSIGNMENT_PATTERN.search(line):
                return "declaration"

    if any(p.search(line) for p in CONTROL_PATTERNS):
        return "logic"

    if ASSIGNMENT_PATTERN.search(line):
        return "logic"

    if CALL_PATTERN.search(line):
        return "logic"

    return "logic"


def fine_to_coarse(label: FineLabel):
    if label in ["logic", "input", "output"]:
        return label
    
    return "other"


def classify_code_lines(code: str) -> list[str]:
    # result: dict[int, dict[str, str]] = {}
    result = []
    lines = code.splitlines()

    for i, line in enumerate(lines, start=1):
        fine = classify_fine_line(line)
        coarse = fine_to_coarse(fine)
        result.append(coarse)

    return result