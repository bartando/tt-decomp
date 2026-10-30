"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_rmc_drawable_draw_lod_models_mutations.py

Patch build-cache copies only. Each mutation must produce behavioral FAIL
(exit 1); BUILD, SPEC and UNSUPPORTED do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("select a different LOD", "ModelList* list = lists[lod];", "ModelList* list = lists[(lod + 1) % 4];"),
    ("start transform cache at zero", "int currentTransform = -2;", "int currentTransform = 0;"),
    ("truncate list count", "i < list->count;", "i < static_cast<uint8_t>(list->count);"),
    ("cache count across draw callbacks", "uint32_t i = 0; i < list->count;",
     "uint32_t i = 0, count = list->count; i < count;"),
    ("cache backing array across draw callbacks", "int currentTransform = -2;",
     "auto** cachedModels = list->models;\n    int currentTransform = -2;"),
    ("wrong mask word", "transformIndex >> 5", "(transformIndex >> 5) ^ 1"),
    ("wrong mask bit", "transformIndex & 31", "(transformIndex + 1) & 31"),
    ("invert mask filter", "(1u << (transformIndex & 31))) == 0",
     "(1u << (transformIndex & 31))) != 0"),
    ("read adjacent transform byte", "transformIndex = model[0x13]", "transformIndex = model[0x12]"),
    ("normalize model skin flag incorrectly", "model[0x15] != 0", "model[0x15] == 1"),
    ("use all skinning argument bits", "static_cast<uint8_t>(skinned) != 0", "skinned != 0"),
    ("swap skin and draw contexts", "model, skinContext, shaderGroup, transforms,",
     "model, drawContext, shaderGroup, transforms,"),
    ("use transform index as geometry filter", "model[0x10], drawContext, lod);",
     "model[0x13], drawContext, lod);"),
    ("only recognize canonical identity flag", "model[0x18] != 0", "model[0x18] == 1"),
    ("always reinstall rigid matrices", "if (currentTransform != wantedTransform)", "if (true)"),
    ("use 48-byte transform stride", "transforms + transformIndex * 16", "transforms + transformIndex * 12"),
    ("omit rigid shader matrix update", "if (lbl_8260633D != 0)", "if (false)"),
    ("omit rigid draw", "fragDrawable_19C8_h(model, shaderGroup, drawContext, lod);", ""),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/rage_grm.cpp").read_text()
    spec = Path(__file__).with_name("rmc_drawable_draw_lod_models.py")
    caught = 0
    for name, old, new in MUTATIONS:
        expected = 2 if name in ("use transform index as geometry filter", "use 48-byte transform stride") else 1
        assert source.count(old) == expected, f"mutation anchor changed: {name}"
        patches = ((old, new),)
        if name == "cache backing array across draw callbacks":
            patches += (("uint8_t* model = list->models[i];", "uint8_t* model = cachedModels[i];"),)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=1000, seed=1, patches=patches)).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
