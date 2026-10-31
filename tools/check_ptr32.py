#!/usr/bin/env python3
"""Check added C++ lines for game-pointer hazards: [BASE..HEAD | BASE...HEAD]."""

import argparse
import bisect
from pathlib import Path
import re
import subprocess


def git(*args):
    return subprocess.check_output(
        ["git", "-c", "core.quotepath=false", *args], text=True
    )


def added_lines(diff):
    files = {}
    path = None
    line = 0
    for entry in diff.splitlines():
        if entry.startswith("+++ "):
            path = entry[6:] if entry.startswith("+++ b/") else None
        elif entry.startswith("@@ "):
            line = int(re.search(r"\+(\d+)", entry).group(1))
        elif entry.startswith("+") and path:
            files.setdefault(path, set()).add(line)
            line += 1
        elif not entry.startswith(("-", "\\")):
            line += 1
    return files


def mask_comments_and_strings(source):
    # Keep offsets/newlines so diagnostics still refer to the real source.
    return re.sub(
        r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
        lambda m: re.sub(r"[^\n]", " ", m.group()), source,
    )


def violations(source, added):
    code = mask_comments_and_strings(source)
    starts = [0] + [m.end() for m in re.finditer("\n", source)]

    def line_at(offset):
        return bisect.bisect_right(starts, offset)

    findings = set()

    def report(start, end, message):
        diagnostic = line_at(start)
        # Include the whole statement so multiline casts and host annotations work.
        start = max(code.rfind(";", 0, start), code.rfind("{", 0, start),
                    code.rfind("}", 0, start)) + 1
        terminator = code.find(";", start)
        end = terminator + 1 if terminator >= 0 else end
        first, last = line_at(start), line_at(end - 1)
        lines = source.splitlines()
        if "ptr32-check: host" in "\n".join(lines[first - 1:last]):
            return
        changed = added.intersection(range(first, last + 1))
        if changed:
            findings.add((diagnostic, message))

    for match in re.finditer(r"\b(?:u?intptr_t)\b", code):
        report(match.start(), match.end(), "pointer/integer conversion: use ptr32<T> or load_ptr32<T>")

    # Also catch direct casts of explicit 32-bit loads, without uintptr_t.
    for match in re.finditer(
        r"(?:reinterpret_cast\s*<[^;{}]*?\*>|\([^;{}()]*?\*+\))"
        r"\s*\(*\s*\*[^;{}]*?\b(?:u?int32_t)\b", code
    ):
        report(match.start(), match.end(), "32-bit integer pointer load: use load_ptr32<T>")

    # Only direct class/struct members, not parameters, returns or local variables.
    tokens = re.compile(r"[{}]|\bvoid\s*\*+\s*(?:const\s+)?\w+\s*"
                        r"(?:\[[^\]]*\]\s*)*(?:=[^;{}]*)?;")
    scopes = []
    previous_brace = 0
    for match in tokens.finditer(code):
        token = match.group()
        if token == "{":
            prefix = code[previous_brace:match.start()]
            scopes.append(bool(re.search(r"\b(?:struct|class)\s+\w+[^;{}]*$", prefix)))
            previous_brace = match.end()
        elif token == "}":
            if scopes:
                scopes.pop()
            previous_brace = match.end()
        elif scopes and scopes[-1]:
            report(match.start(), match.end(), "native void* member: use ptr32<T> in game layouts")

    return sorted(findings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("range", nargs="?", help="git diff range; default: HEAD versus working tree")
    args = parser.parse_args()
    revision = None
    if args.range:
        separator = "..." if "..." in args.range else ".."
        if separator not in args.range:
            parser.error("expected BASE..HEAD or BASE...HEAD")
        revision = args.range.split(separator, 1)[1] or "HEAD"
    root = Path(git("rev-parse", "--show-toplevel").strip())
    diff = git("-C", str(root), "diff", "--no-ext-diff", "--no-renames", "--no-color", "--unified=0",
               args.range or "HEAD", "--", "src/", "include/")
    count = 0
    for path, added in added_lines(diff).items():
        if Path(path).suffix not in {".h", ".hpp", ".hh", ".hxx", ".c", ".cpp", ".cc", ".cxx"}:
            continue
        # This is the implementation of the conversion boundary itself.
        if path == "include/rage/ptr32.hpp":
            continue
        source = git("show", f"{revision}:{path}") if revision else (root / path).read_text()
        for line, message in violations(source, added):
            print(f"{path}:{line}: {message}")
            count += 1
    if not count:
        print("ptr32: no new pointer hazards found")
    return int(count != 0)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode)
