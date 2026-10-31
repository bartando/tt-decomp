"""Only behavioral FAIL counts for font registration, cleanup and ownership."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    "localized_font_construct": ("void* localizedFontConstruct(void* storage) {", [
        ("wrong default size", "font->size = 32;", "font->size = 64;"),
        ("wrong list link", "font->next = previous;", "font->next = nullptr;"),
        ("clear untouched glyph bytes", "font->glyphIndex[0] = 0;", "for (auto& v : font->glyphIndex) v = 0;"),
        ("register every font", "if (!previous)", "if (true)"),
        ("deduplicate nonnull objects", "record.callback == &localizedFontShutdown && !record.object", "record.callback == &localizedFontShutdown"),
        ("wrong shutdown flags", "record.flags = 1;", "record.flags = 2;"),
    ]),
    "localized_font_destroy": ("void localizedFontDestroy(void* raw) {", [
        ("omit cleanup", "localizedFontClearResources(font);", "/* lost cleanup */"),
        ("lose retained tail", "current->next = font->next.get();", "current->next = nullptr;"),
        ("omit name release", "rage_free(font->name.get());", "/* lost name release */"),
        ("test count instead of ownership", "if (font->pages.capacity)", "if (font->pages.count)"),
    ]),
    "localized_font_release": ("void localizedFontRelease(void* raw) {", [
        ("skip zero-count wrap", "if (!font) return;", "if (!font || font->references == 0) return;"),
        ("wrong last-reference test", "if (references == 1)", "if (references == 2)"),
        ("lose retained tail", "current->next = font->next.get();", "current->next = nullptr;"),
        ("omit destruction", "localizedFontDestroy(font);", "/* lost destruction */"),
        ("omit unknown-font diagnostic", "nop_8240E6D0(g_localizedFontReleaseError);", "/* lost diagnostic */"),
    ]),
    "localized_font_shutdown": ("void localizedFontShutdown() {", [
        ("release once", "while (g_localizedFontHead)", "if (g_localizedFontHead)"),
        ("omit shutdown", "while (g_localizedFontHead) localizedFontRelease(g_localizedFontHead.get());", "/* lost shutdown */"),
    ]),
}

CLEAR_CASES = [
    ("omit auxiliary textures", "if (void* texture = font->auxiliaryTextures.data.get()[i].get())",
     "if (void* texture = nullptr)"),
    ("omit auxiliary effects", "if (void* effect = font->auxiliaryEffects.data.get()[i].get())",
     "if (void* effect = nullptr)"),
    ("increment references", "if (--references == 0)", "if (++references == 0)"),
    ("whole-word ownership test", "static_cast<uint8_t>(rage_FindSingleton(pointer)) == 0", "rage_FindSingleton(pointer) == 0"),
    ("retain array capacity", "array.capacity = 0;", "/* lost capacity clear */"),
    ("omit glyph release", "releaseBlock(font->glyphs);", "/* lost glyph release */"),
]


def check(spec, label, old, new):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        rc = Checker(Path(__file__).with_name(spec + ".py"),
                     Options(seed=1, patches=((old, new),))).run()
    first = output.getvalue().splitlines()[0]
    caught = rc == 1 and first.startswith("FAIL ")
    print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
    if not caught:
        print(output.getvalue())
    return caught


def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/localized_font_lifecycle.cpp").read_text()
    total = 0
    for spec, (signature, cases) in CASES.items():
        start = source.index(signature)
        body = source[start:source.index("\n}", start) + 2]
        for label, old, new in cases:
            assert old in body, label
            if not check(spec, label, body, body.replace(old, new)):
                return 1
            total += 1
    for label, old, new in CLEAR_CASES:
        assert old in source, label
        if not check("localized_font_clear_resources", label, old, new):
            return 1
        total += 1
    print(f"Caught {total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
