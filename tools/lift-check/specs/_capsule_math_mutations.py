"""Mutation proof for four misnamed capsule math lifts. From the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_capsule_math_mutations.py

Only build-cache copies are patched. Only behavioral FAIL (exit 1) counts;
BUILD, SPEC and UNSUPPORTED errors never count as detected mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


CASES = {
    "rage_cos_sin": (
        "src/rage/math/ph_math.cpp", "void rage::cosSin(",
        [
            ("truncate double angle", "    *cosine =", "    angle = static_cast<float>(angle);\n    *cosine ="),
            ("cosine in both outputs", "crt_sin(angle)", "crt_cos(angle)"),
            ("wrong sine sign", "crt_sin(angle)", "crt_sin(-angle)"),
            ("omit cosine store", "*cosine = static_cast<float>(crt_cos(angle));", "(void)crt_cos(angle);"),
            ("reverse aliased output writes",
             "    *cosine = static_cast<float>(crt_cos(angle));\n    *sine = static_cast<float>(crt_sin(angle));",
             "    const float c = static_cast<float>(crt_cos(angle));\n    *sine = static_cast<float>(crt_sin(angle));\n    *cosine = c;"),
        ]),
    "rage_mat33_rotation_normalized_axis": (
        "src/rage/math/mat33.cpp", "void mat33RotationNormalizedAxis(",
        [
            ("wrong diagonal square", "axis[1] * axis[1], scale, cosine", "axis[0] * axis[0], scale, cosine"),
            ("wrong off-diagonal sign", "axis[1], sine * axis[2]", "axis[1], -(sine * axis[2])"),
            ("wrong destination entry", "out[8] =", "out[9] ="),
            ("overwrite row padding", "    out[0] =", "    out[3] = 0.0f;\n    out[0] ="),
            ("unfuse diagonal", "__builtin_fmaf(axis[0] * axis[0], scale, cosine)", "(axis[0] * axis[0]) * scale + cosine"),
            ("truncate double angle", "    const float cosine =", "    angle = static_cast<float>(angle);\n    const float cosine ="),
            ("snapshot overlapping axis", "    const float scale =",
             "    float copy[4] = {axis[0], axis[1], axis[2], axis[3]};\n    axis = copy;\n    const float scale ="),
        ]),
    "rage_mat33_rotate_x": (
        "src/rage/math/mat33.cpp", "void mat33RotateX(",
        [
            ("drop input angle", "cosSin(&cosine, &sine, angle);", "cosSin(&cosine, &sine, 0.0);"),
            ("swap cosine and sine", "cosSin(&cosine, &sine, angle);", "cosSin(&sine, &cosine, angle);"),
            ("wrong row subtraction", "ySine - zCosine", "ySine + zCosine"),
            ("omit fourth lane", "lane < 4;", "lane < 3;"),
            ("wrong source row", "flushRotationVmx(matrix[8 + lane])", "flushRotationVmx(matrix[lane])"),
            ("reuse updated row", "flushRotationVmx(zSine + yCosine)", "flushRotationVmx(flushRotationVmx(matrix[8 + lane] * sine) + yCosine)"),
            ("fuse VMX multiply-add", "flushRotationVmx(zSine + yCosine)", "flushRotationVmx(__builtin_fmaf(z, sine, yCosine))"),
            ("omit VMX denormal flushing", "    float cosine, sine;",
             "    auto flushRotationVmx = [](float value) { return value; };\n    float cosine, sine;"),
        ]),
    "rage_expand_aabb_by_offset_box": (
        "src/rage/math/polygon_clip.cpp", "void expandAabbByOffsetBox(",
        [
            ("omit center offset", "flushClipVmx(box[2][lane])", "0.0f"),
            ("wrong full-size argument", "destination, center, box[1]", "destination, center, box[2]"),
            ("count w as size", "bits &= lbl_82619BE0[lane];", "bits &= 0x7fffffffu;"),
            ("preserve denormal sizes", "flushClipVmx(size) == 0.0f", "size == 0.0f"),
            ("merge empty boxes", "if (empty) return;", "/* empty check missing */"),
            ("lose center w", "    mergeAabbCenterSize(destination,", "    center[3] = 0.0f;\n    mergeAabbCenterSize(destination,"),
            ("preserve denormal center inputs", "flushClipVmx(box[0][lane])", "box[0][lane]"),
        ]),
}


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec_name, (source_path, signature, mutations) in CASES.items():
        source = (root / source_path).read_text()
        start = source.index(signature)
        end = source.index("\n}", start) + 2
        body = source[start:end]
        assert source.count(body) == 1, signature
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        total += len(mutations)
        print(f"{spec_name}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
