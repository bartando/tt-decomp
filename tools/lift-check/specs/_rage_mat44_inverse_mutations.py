"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_rage_mat44_inverse_mutations.py

Mutate build-cache copies only; the source lift stays intact. Only behavioral
FAIL (exit 1) counts as caught, never BUILD, SPEC or UNSUPPORTED errors.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("omit reciprocal", "1.0f / mat44Determinant(m)", "mat44Determinant(m)"),
    ("negate reciprocal", "1.0f / mat44Determinant(m)", "-1.0f / mat44Determinant(m)"),
    ("wrong determinant input", "mat44Determinant(m);", "mat44Determinant(m + 4);"),
    ("lose checkerboard signs", "((row + col) & 1) ? -scaled : scaled", "scaled"),
    ("transpose destination", "out[col * 4 + row] =", "out[row * 4 + col] ="),
    ("omit homogeneous column", "col < 4; ++col", "col < 3; ++col"),
    ("reverse cofactor subtraction", "-__builtin_fmaf(af, h, -sum)",
     "__builtin_fmaf(af, h, sum)"),
    ("unfuse minor sum", "__builtin_fmaf(bf, g, sum)", "bf * g + sum"),
    ("lose translation sum order", "row == 0 && col == 3", "false"),
    ("reject singular matrix", "    for (unsigned row = 0; row < 4; ++row)",
     "    if (!__builtin_isfinite(invDet)) return;\n"
     "    for (unsigned row = 0; row < 4; ++row)"),
    ("snapshot overlapping input", "    const float invDet = 1.0f / mat44Determinant(m);",
     "    const float invDet = 1.0f / mat44Determinant(m);\n"
     "    float copy[16];\n"
     "    for (unsigned i = 0; i < 16; ++i) copy[i] = m[i];\n"
     "    m = copy;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/math/mat44.cpp").read_text()
    spec = Path(__file__).with_name("rage_mat44_inverse.py")
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
