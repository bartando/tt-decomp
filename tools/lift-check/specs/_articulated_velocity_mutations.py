"""Run with PYTHONPATH=tools/lift-check and tools/lift-check/.venv/bin/python.

Patches build-cache copies only; every mutation must produce a behavioral FAIL.
Build/spec failures and lift faults never count as caught mutations.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "src/physics/ph_physics.cpp"
COMMON = [
    ("wrong angular cache", "memcpy(body + 0x130 / 4, angular, 16);",
     "memcpy(body + 0x130 / 4, body + 0x110 / 4, 16);"),
    ("reverse point cross product", "pointVelocity[axis] += cross;",
     "pointVelocity[axis] -= cross;"),
    ("omit scalar fused subtraction", "__builtin_fmaf(angular[z], position[y], -product)",
     "angular[z] * position[y] - product"),
]
CASES = {
    "ph_articulated_set_linear_velocity": COMMON + [
        ("wrong root vector", "phFlushVmx(root[0x110 / 4 + lane])",
         "phFlushVmx(root[0x120 / 4 + lane])"),
        ("reverse linear delta", "phFlushVmx(velocity[lane]) - phFlushVmx(root[0x110 / 4 + lane])",
         "phFlushVmx(root[0x110 / 4 + lane]) - phFlushVmx(velocity[lane])"),
    ],
    "ph_articulated_set_angular_velocity": COMMON + [
        ("wrong angular root", "phFlushVmx(root[0x120 / 4 + lane])",
         "phFlushVmx(root[0x110 / 4 + lane])"),
        ("reverse VMX cross product", "phFlushVmx(-(product2 - product1))",
         "phFlushVmx(product2 - product1)"),
        ("omit VMX product flush", "phFlushVmx(phFlushVmx(body[0xC0 / 4 + z]) * delta[y])",
         "body[0xC0 / 4 + z] * delta[y]"),
    ],
}


def main():
    source = (ROOT / SOURCE).read_text()
    total = 0
    for spec, mutations in CASES.items():
        for name, old, new in mutations:
            assert source.count(old) == 1, (spec, name, source.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=600, seed=1, patches=((old, new),))).run()
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
