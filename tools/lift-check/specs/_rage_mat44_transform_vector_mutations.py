"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python
    tools/lift-check/specs/_rage_mat44_transform_vector_mutations.py

Only behavioral failures count; patches affect build-cache copies, not the source.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("wrong matrix element", "m[8], point[2]", "m[9], point[2]"),
    ("wrong point component", "__builtin_fmaf(m[12], point[3], m[4] * point[1])", "__builtin_fmaf(m[12], point[2], m[4] * point[1])"),
    ("omit translation", "m[12 + c], point[3]", "0.0f, point[3]"),
    ("wrong output lane", "out[c] = __builtin_fmaf(m[8 + c]", "out[3 - c] = __builtin_fmaf(m[8 + c]"),
    ("skip last lane", "for (unsigned c = 1; c < 4; ++c) {\n        out[c] = __builtin_fmaf(m[8 + c]", "for (unsigned c = 1; c < 3; ++c) {\n        out[c] = __builtin_fmaf(m[8 + c]"),
    ("unfuse first lane", "out[0] = __builtin_fmaf(point[0], m[0], __builtin_fmaf(m[8], point[2],", "out[0] = (point[0] * m[0] + __builtin_fmaf(m[8], point[2],"),
    ("snapshot point", "void mat44TransformVector(float* out, const float* point, const float* m) {",
     "void mat44TransformVector(float* out, const float* input, const float* m) {\n"
     "    float copy[4] = {input[0], input[1], input[2], input[3]};\n"
     "    const float* point = copy;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/math/mat44.cpp").read_text()
    spec = Path(__file__).with_name("rage_mat44_transform_vector.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
