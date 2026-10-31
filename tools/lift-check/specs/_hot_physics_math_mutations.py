"""Mutation proof: run with PYTHONPATH=tools/lift-check
tools/lift-check/.venv/bin/python tools/lift-check/specs/_hot_physics_math_mutations.py.

Only build-cache copies are patched. Require behavioral FAILs (memory/call/return
differences); build/spec errors and lift faults do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
CASES = {
    "ph_matrix_transpose_multiply3x4": (
        "src/physics/ph_physics.cpp",
        [("translation sign", "phFlushVmx(a[12 + axis]) - phFlushVmx(b[12 + axis])",
          "phFlushVmx(a[12 + axis]) + phFlushVmx(b[12 + axis])"),
         ("wrong basis row", "phDotVmx(input, b + col * 4, 3)",
          "phDotVmx(input, b + ((col + 1) % 3) * 4, 3)"),
         ("clear shuffle W", "memcpy(result + row * 4 + 3, a + row * 4, sizeof(float));",
          "result[row * 4 + 3] = 0.0f;"),
         ("single precision accumulation", "double sum = 0.0;", "float sum = 0.0f;"),
         ("omit input flush", "phFlushVmx(a[lane])) * phFlushVmx(b[lane])",
          "a[lane]) * b[lane]"),
         ("omit output flush", "return phFlushVmx(static_cast<float>(sum));",
          "return static_cast<float>(sum);")]),
    "ph_bound_transform_centroid": (
        "src/physics/ph_physics.cpp",
        [("wrong centroid offset", "memcpy(point, bound + 12, sizeof(point));",
          "memcpy(point, bound, sizeof(point));"),
         ("drop translation", "point[3] = 1.0f;", "point[3] = 0.0f;"),
         ("transpose basis", "{matrix[axis], matrix[4 + axis],\n                                 matrix[8 + axis], matrix[12 + axis]}",
          "{matrix[axis * 4], matrix[axis * 4 + 1], matrix[axis * 4 + 2], matrix[12 + axis]}"),
         ("clear shuffle W", "memcpy(result + 3, point, sizeof(float));", "result[3] = 0.0f;"),
         ("omit input flush", "phFlushVmx(a[lane])) * phFlushVmx(b[lane])",
          "a[lane]) * b[lane]"),
         ("omit output flush", "return phFlushVmx(static_cast<float>(sum));",
          "return static_cast<float>(sum);")]),
    "rage_clip_aabb_to_active_camera": (
        "src/rage/math/polygon_clip.cpp",
        [("wrong camera stride", "cameras + frame * 912", "cameras + frame * 896"),
         ("wrong matrix offset", "reinterpret_cast<const float (*)[4]>(camera + 64)",
          "reinterpret_cast<const float (*)[4]>(camera + 80)"),
         ("reverse near selection", "cap - nearClip >= 0.0f ? nearClip : static_cast<float>(fallback)",
          "cap - nearClip < 0.0f ? nearClip : static_cast<float>(fallback)"),
         ("drop reference", "0, 0, 0, 0, referencePoint, selectedNear,",
          "0, 0, 0, 0, nullptr, selectedNear,"),
         ("discard return", "return clipAabbToFrustum(context, box, reinterpret_cast",
          "return !clipAabbToFrustum(context, box, reinterpret_cast")]),
}


# Specs whose anchors also occur in other functions of the same file: mutate
# only inside the named definition.
SCOPES = {"ph_bound_transform_centroid": "void phBound_TransformCentroid("}


def main():
    for spec, (source_path, mutations) in CASES.items():
        source = (ROOT / source_path).read_text()
        body = None
        if spec in SCOPES:
            start = source.index("\n" + SCOPES[spec]) + 1
            body = source[start:source.index("\n}\n", start) + 2]
        for name, old, new in mutations:
            if body is not None and body.count(old) == 1:
                patch = (body, body.replace(old, new))
            else:
                assert source.count(old) == 1, (spec, name)
                patch = (old, new)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=1200, seed=1, patches=(patch,))).run()
            report = output.getvalue()
            caught = rc == 1 and "the lift faulted" not in report
            print(f"{spec}: {'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
        print(f"{spec}: caught {len(mutations)}/{len(mutations)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
