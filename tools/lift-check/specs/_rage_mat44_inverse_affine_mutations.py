"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_rage_mat44_inverse_affine_mutations.py

Only build-cache copies are mutated. Require behavioral FAIL (exit 1), never
count BUILD, SPEC or UNSUPPORTED errors as a caught mutation.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("accept boundary determinant", "__builtin_fabsf(det) <= maxBasis * 3.6e-7f",
     "__builtin_fabsf(det) < maxBasis * 3.6e-7f"),
    ("omit absolute determinant", "__builtin_fabsf(det) <= maxBasis * 3.6e-7f",
     "det <= maxBasis * 3.6e-7f"),
    ("use fixed tolerance", "maxBasis * 3.6e-7f", "3.6e-7f"),
    ("use cubed scale tolerance", "maxBasis * 3.6e-7f", "maxBasis * maxBasis * maxBasis * 3.6e-7f"),
    ("lose cofactor sign", "const float x1 = -(invDet * c01);",
     "const float x1 = invDet * c01;"),
    ("transpose inverse basis", "out[8] = x2;\n    out[4] = x1;",
     "out[4] = x2;\n    out[8] = x1;"),
    ("omit translation", "out[12] = -__builtin_fmaf(m[14], x2,",
     "out[12] = 0.0f * __builtin_fmaf(m[14], x2,"),
    ("reverse translation sign", "out[13] = -__builtin_fmaf(m[14], y2,",
     "out[13] = __builtin_fmaf(m[14], y2,"),
    ("overwrite homogeneous lane", "    out[10] = z2;",
     "    out[15] = 1.0f;\n    out[10] = z2;"),
    ("write on rejection", "        return false;",
     "        return (out[0] = 0.0f, false);"),
    ("wrong success return", "    return true;", "    return false;"),
    ("snapshot aliased input", "bool mat44InverseAffine(float* out, const float* m) {",
     "bool mat44InverseAffine(float* out, const float* input) {\n"
     "    float copy[16];\n"
     "    for (unsigned i = 0; i < 16; ++i) copy[i] = input[i];\n"
     "    const float* m = copy;"),
    ("unfuse cofactor", "__builtin_fmaf(m[5], m[10], -(m[6] * m[9]))",
     "m[5] * m[10] - m[6] * m[9]"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/math/mat44.cpp").read_text()
    spec = Path(__file__).with_name("rage_mat44_inverse_affine.py")
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
