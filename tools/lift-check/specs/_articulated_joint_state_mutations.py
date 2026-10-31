"""Behavioral mutation checks for clearing, joint propagation, and root rebasing.

Patches checker build-cache copies only. Build/spec errors and lift faults do
not count. Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "src/physics/ph_physics.cpp"
CASES = {
    "ph_articulated_clear_velocities": ("void phArticulatedCollider_ResetForceAccumulators(void* jointData) {", [
        ("leave cached point velocity", "memset(body + 0x110, 0, 64);", "memset(body + 0x110, 0, 48);"),
        ("leave saved point velocity", "memset(body + 0x3F0, 0, 64);", "memset(body + 0x3F0, 0, 48);"),
        ("wrong joint virtual", "joint->ClearVelocityConstraints();", "joint->ClearForceConstraints();"),
        ("skip last child", "i < childCount;", "i + 1 < childCount;"),
    ]),
    "ph_articulated_propagate_motion": ("void phArticulatedCollider_8450(void* jointData) {", [
        ("skip propagation", "joint->PropagateMotion();", "(void)joint;"),
        ("cache before propagation", "joint->PropagateMotion();\n        phRefreshJointVelocity(body);",
         "phRefreshJointVelocity(body);\n        joint->PropagateMotion();"),
        ("cache wrong body", "data[11 + i]", "data[10 + i]"),
        ("drop caches", "phRefreshJointVelocity(body);", "(void)body;"),
    ]),
    "ph_articulated_rebase_from_root": ("void phArticulatedCollider_F0E0(void* collider) {", [
        ("omit transpose", "rootTransform + lane * 4 + row", "rootTransform + row * 4 + lane"),
        ("drop world position accumulation", "phFlushVmx(output[0xD0 / 4 + lane]) + phFlushVmx(rootTransform[12 + lane])",
         "phFlushVmx(rootTransform[12 + lane])"),
        ("reverse rebasing delta", "phFlushVmx(lbl_82606750[lane]) - phFlushVmx(rootTransform[12 + lane])",
         "phFlushVmx(rootTransform[12 + lane]) - phFlushVmx(lbl_82606750[lane])"),
        ("use current angular velocity", "const float* angular = body + 0x130 / 4;",
         "const float* angular = body + 0x120 / 4;"),
        ("reverse cached point correction", "body[0x140 / 4 + axis] += cross;",
         "body[0x140 / 4 + axis] -= cross;"),
    ]),
}


def main():
    source = (ROOT / SOURCE).read_text()
    total = 0
    for spec, (signature, mutations) in CASES.items():
        start = source.index(signature)
        body = source[start:source.index('\n}\n', start) + 2]
        for name, old, new in mutations:
            assert body.count(old) == 1, (spec, name, body.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=600, seed=1, patches=((body, body.replace(old, new)),))).run()
            report = output.getvalue()
            caught = rc == 1 and "the lift faulted" not in report
            print(f"{spec}: {'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
