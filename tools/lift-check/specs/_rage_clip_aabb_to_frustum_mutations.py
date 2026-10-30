"""Run from the repo root with PYTHONPATH=tools/lift-check and its venv Python.

Patch build-cache copies only. Every mutation must produce behavioral FAIL (1);
BUILD, SPEC, UNSUPPORTED and exceptions do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("treat one flat dimension as empty",
     "empty &= flushClipVmx(extent) == 0.0f;",
     "if (lane < 3 && flushClipVmx(extent) == 0.0f) return false;\n"
     "        empty &= flushClipVmx(extent) == 0.0f;"),
    ("zero an initially empty input", "    if (empty)\n        return false;",
     "    if (empty) { __builtin_memset(box, 0, 48); return false; }"),
    ("omit eighth corner", "corner < 8;", "corner < 7;"),
    ("put homogeneous w in scratch lane", "point[3] = homogeneous[0];", "point[3] = homogeneous[3];"),
    ("transpose matrix during point transform", "flushClipVmx(matrix[row][axis])",
     "flushClipVmx(matrix[axis][row])"),
    ("omit translation", "row < 4;", "row < 3;"),
    ("round each dot-product accumulation", "double sum = 0.0;", "float sum = 0.0f;"),
    ("reverse near-plane cap", "0.1f - nearClip >= 0.0f ? nearClip : 0.1f",
     "nearClip - 0.1f >= 0.0f ? nearClip : 0.1f"),
    ("reverse each face's vertices", "face * 4 + vertex", "face * 4 + (3 - vertex)"),
    ("omit sixth face", "face < 6;", "face < 5;"),
    ("discard optional reference point",
     "clipped, planes, referencePoint);", "clipped, planes, nullptr);"),
    ("omit final clipped vertex", "vertex < count;", "vertex < count - 1;"),
    ("use ordered minimum for unordered values", "!(minimum[axis] < value)", "minimum[axis] > value"),
    ("use ordered maximum for unordered values", "!(maximum[axis] > value)", "maximum[axis] < value"),
    ("leave auxiliary vector on rejection", "vector < 3;", "vector < 2;"),
    ("return half extents", "box[1][axis] = flushClipVmx(hi - lo);",
     "box[1][axis] = flushClipVmx((hi - lo) * 0.5f);"),
    ("omit center halving", "box[0][axis] = flushClipVmx(sum * 0.5f);",
     "box[0][axis] = sum;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/math/polygon_clip.cpp").read_text()
    spec = Path(__file__).with_name("rage_clip_aabb_to_frustum.py")
    # A broken baseline must never make every mutation look successfully caught.
    if Checker(spec, Options(trials=200, seed=1)).run() != 0:
        return 1
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=200, seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
