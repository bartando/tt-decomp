"""Mutation proof; patches affect build-cache copies only.

Run: PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_grm_draw_queue_mutations.py
Only behavioral FAIL (exit 1), never build/spec/unsupported errors, counts.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
MUTATIONS = [
    ("omit shader registration", "shaderIndex = arrays[0].count;", "/* missing shader index */"),
    ("omit shader count", "++arrays[0].count;", "/* missing shader count */"),
    ("omit previous tail link", "arrays[1].entries[bucket->next].next = drawIndex;", "/* broken draw chain */"),
    ("omit bucket tail", "bucket->next = drawIndex;", "/* stale bucket tail */"),
    ("overwrite existing head", "if (bucket->firstOrIndex == 0) {", "if (true) {"),
    ("omit draw count", "++arrays[1].count;", "/* missing draw count */"),
    ("store shader as model", "draw.object = model;", "draw.object = shader;"),
    ("leave random next link", "draw.next = 0;", "/* unterminated draw chain */"),
    ("wrong geometry halfword", "static_cast<uint16_t>(geometryIndex);", "static_cast<uint16_t>(geometryIndex >> 16);"),
]


def main():
    spec = Path(__file__).with_name("grm_draw_queue_add_geometry.py")
    source = (ROOT / "src/rage/rage_grm.cpp").read_text()
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, name
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=128, seed=1, patches=((old, new),))).run()
        print(f"grm_draw_queue_add_geometry: {'CAUGHT' if rc == 1 else 'MISSED'} {name}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"grm_draw_queue_add_geometry: caught {len(MUTATIONS)}/{len(MUTATIONS)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
