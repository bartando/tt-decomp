#!/usr/bin/env python3
"""Compare full lld/MinGW and Apple ld missing-symbol diagnostics."""
import re
import sys
from pathlib import Path


def inventory(path, pattern):
    log = Path(path).read_text()
    symbols = set(re.findall(pattern, log, re.MULTILINE))
    if not symbols and ("error:" in log or "FAILED:" in log):
        raise SystemExit(f"{path}: build failed without a complete undefined-symbol inventory")
    if "too many errors emitted" in log:
        raise SystemExit(f"{path}: truncated linker errors; use --error-limit=0")
    return symbols


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: compare-native-undefined.py WIN32_LOG MACOS_LOG")
    windows = inventory(sys.argv[1], r"^ld\.lld: error: undefined symbol: (.+)$")
    macos = inventory(sys.argv[2], r'^  "(.*?)", referenced from:')
    for target, symbols in (("win32", windows), ("macos", macos)):
        output = Path(f"/tmp/tt-{target}-undefined.txt")
        output.write_text("".join(f"{symbol}\n" for symbol in sorted(symbols)))
        print(f"{target}: {len(symbols)} distinct undefined symbols ({output})")
    for target, unique in (("win32", windows - macos), ("macos", macos - windows)):
        print(f"{target} only ({len(unique)}):")
        for symbol in sorted(unique):
            print(f"  {symbol}")
