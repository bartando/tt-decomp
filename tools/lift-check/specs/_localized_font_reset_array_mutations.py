"""Require behavioral failures for reset ordering/TLS and array allocation."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    "localized_font_reset": ("src/rage/localized_font_lifecycle.cpp", "void localizedFontReset(void* raw, uint32_t /*flags*/, const char* /*name*/) {", [
        ("clear old name before allocation", "freeBlock(font->name.get());", "releaseBlock(font->name);"),
        ("omit TLS initialization", "sysMemAllocator_InitThreadHeap();", "/* lost init */"),
        ("omit default string copy", "std::memcpy(name, g_localizedFontResetName, bytes)", "std::memset(name, 0, bytes)"),
        ("reload changed TLS root", "rage::load_ptr32<FontAllocator>(thread, 4)->Free(glyphs);", "currentFontAllocator()->Free(glyphs);"),
        ("leave glyph index entries", "std::memset(font->glyphIndex, 0, sizeof(font->glyphIndex));", "font->glyphIndex[0] = 0;"),
        ("leave glyph count", "font->glyphCount = 0;", "/* lost count clear */"),
    ]),
    "localized_font_resize_array": ("src/rage/localized_font_array.cpp", "void localizedFontResizeArray(void* array, uint32_t count) {", [
        ("reallocate owned arrays", "if (capacity == 0)", "if (capacity <= 1)"),
        ("allocate truncated count", "rage_Alloc(count > 0x3FFFFFFFu ? UINT32_MAX : count * 4)", "rage_Alloc(uint32_t(storedCount) * 4)"),
        ("retain zero capacity", "std::memcpy(bytes + 6, &storedCount, sizeof(storedCount));", "std::memcpy(bytes + 6, &capacity, sizeof(capacity));"),
        ("omit count store", "std::memcpy(bytes + 4, &storedCount, sizeof(storedCount));", "/* lost count store */"),
    ]),
}


def main():
    root = Path(__file__).resolve().parents[3]
    for spec, (path, signature, cases) in CASES.items():
        source = (root / path).read_text()
        start = source.index(signature)
        body = source[start:source.index("\n}", start) + 2]
        for label, old, new in cases:
            assert body.count(old) == 1, label
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            first = output.getvalue().splitlines()[0]
            caught = rc == 1 and first.startswith("FAIL ")
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(output.getvalue())
                return 1
    print(f"Caught {sum(len(x[2]) for x in CASES.values())} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
