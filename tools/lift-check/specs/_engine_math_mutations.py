"""Behavioral proof for restored engine math entry points.
Run with PYTHONPATH=tools/lift-check and .venv/bin/python from repo root.
Patch only build-cache copies of the named function. Only a behavioral FAIL
counts; BUILD/SPEC/UNSUPPORTED, faults, or surviving mutants fail the runner.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("ph_build_rotation_matrix_x", "src/rage/math/mat33.cpp", "void mat33RotationX(", [
        ("truncate angle", "crt_cos(angle)", "crt_cos(static_cast<float>(angle))"),
        ("reverse rotation", "matrix[9] = -sine;", "matrix[9] = sine;"),
        ("lose cosine", "matrix[5] = cosine;", "matrix[5] = 0.0f;"),
        ("clobber padding", "matrix[10] = cosine;", "matrix[10] = cosine; matrix[11] = 0.0f;"),
    ]),
    ("ph_build_rotation_matrix_y", "src/rage/math/mat33.cpp", "void mat33RotationY(", [
        ("truncate angle", "crt_cos(angle)", "crt_cos(static_cast<float>(angle))"),
        ("reverse rotation", "matrix[2] = -sine;", "matrix[2] = sine;"),
        ("lose identity axis", "matrix[5] = 1.0f;", "matrix[5] = 0.0f;"),
        ("clobber padding", "matrix[10] = cosine;", "matrix[10] = cosine; matrix[11] = 0.0f;"),
    ]),
    ("ph_build_rotation_matrix_z", "src/rage/math/mat33.cpp", "void mat33RotationZ(", [
        ("truncate angle", "crt_sin(angle)", "crt_sin(static_cast<float>(angle))"),
        ("reverse rotation", "matrix[4] = -sine;", "matrix[4] = sine;"),
        ("wrong fixed axis", "matrix[10] = 1.0f;", "matrix[10] = 0.0f;"),
        ("clobber padding", "matrix[10] = 1.0f;", "matrix[10] = 1.0f; matrix[11] = 0.0f;"),
    ]),
    ("rage_mat44_determinant", "src/rage/math/mat44.cpp", "float mat44Determinant(", [
        ("drop cofactor", "const float first = __builtin_fmaf(m[0], c0, -(m[1] * c1));", "const float first = -(m[1] * c1);"),
        ("wrong alternating sign", "-(m[1] * c1)", "m[1] * c1"),
        ("wrong final sign", "return -__builtin_fmaf(m[3], c3, -third);", "return __builtin_fmaf(m[3], c3, third);"),
        ("wrong minor ordering", "m[12], m[13], m[14], false)", "m[12], m[13], m[14], true)"),
    ]),
    ("xaudio_uint64_to_double", "src/platform/audio_frame.cpp", "double XAudio_UInt64ToDouble(", [
        ("round discarded bits", "const uint64_t bits = (uint64_t(1086 - leading) << 52) | fraction;", "uint64_t bits = (uint64_t(1086 - leading) << 52) | fraction;\n    if (leading < 11 && (value & ((uint64_t(1) << (11 - leading)) - 1))) ++bits;"),
        ("wrong exponent", "1086 - leading", "1085 - leading"),
        ("lose fraction bits", ">> 11", ">> 12"),
        ("wrong zero result", "if (value == 0) return 0.0;", "if (value == 0) return 1.0;"),
    ]),
]

def main():
    total = 0
    root = Path(__file__).resolve().parents[3]
    for spec, path, signature, mutations in CASES:
        source = (root / path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, (spec, label)
            report = io.StringIO()
            with contextlib.redirect_stdout(report):
                rc = Checker(Path(__file__).with_name(spec + ".py"), Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            output = report.getvalue()
            caught = rc == 1 and "faulted" not in output
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {output.splitlines()[0]}", flush=True)
            if not caught:
                print(output)
                return 1
            total += 1
    print(f"Caught {total}/{total} behavioral mutations", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
