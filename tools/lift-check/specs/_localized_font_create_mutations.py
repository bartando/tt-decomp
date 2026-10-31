"""Behavioral mutation checks for normalization and font fallback ownership."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("keep uppercase", "character + ('a' - 'A')", "character"),
    ("wrong object size", "heap->Allocate(0x17C, 16)", "heap->Allocate(0x178, 16)"),
    ("wrong alignment", "heap->Allocate(0x17C, 16)", "heap->Allocate(0x17C, 4)"),
    ("whole-word first status", "static_cast<uint8_t>(localizedFontLoad(font, normalized, 0))", "localizedFontLoad(font, normalized, 0)"),
    ("whole-word fallback status", "static_cast<uint8_t>(localizedFontLoad(font, g_localizedFallbackFont, 0))",
     "localizedFontLoad(font, g_localizedFallbackFont, 0)"),
    ("retry requested name", "localizedFontLoad(font, g_localizedFallbackFont, 0)", "localizedFontLoad(font, normalized, 0)"),
    ("omit destruction", "localizedFontDestroy(font);", "/* lost destroy */"),
    ("leak replaced name", "rage_free(fontName.get());", "/* lost old name */"),
    ("store fallback name", "rage_strDuplicate(normalized)", "rage_strDuplicate(g_localizedFallbackFont)"),
    ("wrong name offset", "+ 0x170);", "+ 0x16C);"),
]


def main():
    for label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("localized_font_create.py"),
                         Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if caught else 'MISSED'} {label}: {first}", flush=True)
        if not caught:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
