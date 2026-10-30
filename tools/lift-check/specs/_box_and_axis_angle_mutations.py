"""Mutation proof for the two misnamed capsule lifts. From the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_box_and_axis_angle_mutations.py

Only build-cache copies are patched. Only behavioral FAIL (exit 1) counts;
build/spec/unsupported errors cannot masquerade as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


CASES = {
    "rage_build_box_corners": (
        "src/rage/math/polygon_clip.cpp",
        [
            ("treat full size as half size", "flushClipVmx(size[lane]) * 0.5f", "flushClipVmx(size[lane]) * 1.0f"),
            ("use x size for all axes", "flushClipVmx(size[lane]) * 0.5f", "flushClipVmx(size[0]) * 0.5f"),
            ("swap x corner order", "(corner & 1) ? halfSize[0] : -halfSize[0]", "(corner & 2) ? halfSize[0] : -halfSize[0]"),
            ("reverse front and back", "(corner & 4) ? -halfSize[2] : halfSize[2]", "(corner & 4) ? halfSize[2] : -halfSize[2]"),
            ("leave last corner at center", "for (unsigned corner = 0; corner < 8; ++corner) {\n        out[corner][0] +=", "for (unsigned corner = 0; corner < 7; ++corner) {\n        out[corner][0] +="),
            ("copy an array instead of broadcasting center",
             "__builtin_memcpy(out[corner], origin, sizeof(origin));",
             "__builtin_memcpy(out[corner], center + corner * 4, sizeof(origin));"),
            ("omit fourth lane copy", "__builtin_memcpy(out[corner], origin, sizeof(origin));",
             "__builtin_memcpy(out[corner], origin, 3 * sizeof(float));"),
            ("preserve denormal half sizes", "flushClipVmx(flushClipVmx(size[lane]) * 0.5f)", "size[lane] * 0.5f"),
            ("overwrite center w", "out[corner][2] += (corner & 4) ? -halfSize[2] : halfSize[2];",
             "out[corner][2] += (corner & 4) ? -halfSize[2] : halfSize[2]; out[corner][3] = 1.0f;"),
        ]),
    "rage_mat33_rotation_axis_angle": (
        "src/rage/math/mat33.cpp",
        [
            ("wrong identity diagonal", "out[5] = 1.0f;", "out[5] = 0.0f;"),
            ("clobber identity padding", "out[0] = 1.0f;", "out[3] = 0.0f; out[0] = 1.0f;"),
            ("truncate double angle", "if (angle == 0.0) {", "angle = static_cast<float>(angle);\n    if (angle == 0.0) {"),
            ("dispatch Z to Y", "mat33RotationZ(out, z > 0.0f ? angle : -angle);", "mat33RotationY(out, z > 0.0f ? angle : -angle);"),
            ("lose negative Z sign", "z > 0.0f ? angle : -angle", "angle"),
            ("lose negative Y sign", "y > 0.0f ? angle : -angle", "angle"),
            ("lose negative X sign", "x > 0.0f ? angle : -angle", "angle"),
            ("miss unordered axis sign", "z > 0.0f ? angle : -angle", "z <= 0.0f ? -angle : angle"),
            ("include w in axis length", "lane < 3; ++lane)\n        dot +=", "lane < 4; ++lane)\n        dot +="),
            ("omit zero-length reciprocal guard", "if (reciprocal == __builtin_inff()) reciprocal = 0.0f;", "/* unguarded infinite reciprocal */"),
            ("omit reciprocal refinement", "const float scale = flushRotationVmx(correction + reciprocal);", "const float scale = reciprocal;"),
            ("clear normalized fourth lane", "mat33RotationNormalizedAxis(out, normalized, angle);", "normalized[3] = 0.0f;\n    mat33RotationNormalizedAxis(out, normalized, angle);"),
            ("omit final normalization", "flushRotationVmx(vector[lane] * scale)", "vector[lane]"),
            ("preserve VMX denormals", "bits &= 0x80000000u;", "/* denormals incorrectly preserved */"),
        ]),
}


def main():
    total = 0
    for spec_name, (source_path, mutations) in CASES.items():
        source = (Path(__file__).resolve().parents[3] / source_path).read_text()
        for label, old, new in mutations:
            assert source.count(old) == 1, f"mutation anchor changed: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
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
