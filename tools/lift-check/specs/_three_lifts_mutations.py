"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python this file.
Patches affect build-cache copies only; only behavioral FAIL counts as caught.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
CASES = {
    "cm_cached_operator_get_float": (
        "src/rage/misc/rage_cm.cpp",
        [("cache mask", "(node->flags & 0x30) == 0", "(node->flags & 0x20) == 0"),
         ("recursion flag", "node->flags |= 0x10;", "node->flags |= 0x08;"),
         ("cache valid flag", "(node->flags | 0x20) & ~0x10u", "(node->flags | 0x40) & ~0x10u"),
         ("dispatch dimension", "node->value, &node->port, 0)", "node->value, &node->port, 1)")]),
    "xaudio_effect_update_buffer": (
        "src/rage/audio/xaudio_effect.cpp",
        [("flag mask", "effect->flags & 4", "effect->flags & 8"),
         ("counter decrement", "--effect->remaining;", "++effect->remaining;"),
         ("stop argument", "effect, 1, 1);", "effect, 0, 1);"),
         ("callback buffer", "effect->callbackContext, effect->buffer", "effect->buffer, effect->buffer"),
         ("skip callback", "if (effect->callback)", "if (false)")]),
    "rage_clip_line_to_frustum": (
        "src/rage/math/polygon_clip.cpp",
        [("plane count", "plane < 6; ++plane) {\n        if (referencePoint) {\n            float dot", "plane < 5; ++plane) {\n        if (referencePoint) {\n            float dot"),
         ("reference sign", "if (dot - planes[plane][3] > lbl_8202D110)", "if (dot - planes[plane][3] < lbl_8202D110)"),
         ("initial count", "int32_t count = 2;\n    for (int plane", "int32_t count = 1;\n    for (int plane"),
         ("omit copy", "__builtin_memcpy(scratch, output, static_cast<unsigned>(count) * sizeof(scratch[0]));\n    }\n}\n\n// clipAabb", "(void)output;\n    }\n}\n\n// clipAabb")]),
}


def main():
    for spec_name, (source_path, mutations) in CASES.items():
        source = (ROOT / source_path).read_text()
        caught = 0
        for name, old, new in mutations:
            assert source.count(old) == 1, name
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(trials=128, seed=1, patches=((old, new),))).run()
            print(f"{spec_name}: {'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            caught += 1
        print(f"{spec_name}: caught {caught}/{len(mutations)}", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
