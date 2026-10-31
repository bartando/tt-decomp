"""Break clamping/damping and saved velocity restoration in build-cache copies.

Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python.
Every mutation must cause a behavioral FAIL; build/spec errors and faults fail.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "src/physics/ph_physics.cpp"
CASES = {
    "ph_articulated_clamp_damp_velocities": [
        ("use dot4 for speed", "phDotVmx(velocity, velocity, 3)", "phDotVmx(velocity, velocity, 4)"),
        ("swap speed limits", "phClampBodyVelocity(angular, angularLimit, angularLimitSquared);",
         "phClampBodyVelocity(angular, linearLimit, linearLimitSquared);"),
        ("skip clamping", "if (lengthSquared > limitSquared)", "if (false)"),
        ("wrong damping sign", "-__builtin_fmaf(timestep, lbl_8202CFE8[0], -g_phClampMax)",
         "__builtin_fmaf(timestep, lbl_8202CFE8[0], g_phClampMax)"),
        ("drop angular damping", "angular[lane] = phFlushVmx(phFlushVmx(angular[lane]) * phFlushVmx(damping));",
         "angular[lane] = angular[lane];"),
        ("drop linear damping", "linear[lane] = phFlushVmx(phFlushVmx(linear[lane]) * phFlushVmx(damping));",
         "linear[lane] = linear[lane];"),
        ("scale xyz only", "velocity[lane] = phFlushVmx(phFlushVmx(velocity[lane]) * phFlushVmx(scale));",
         "if (lane < 3) velocity[lane] = phFlushVmx(phFlushVmx(velocity[lane]) * phFlushVmx(scale));"),
    ],
    "ph_articulated_restore_velocities": [
        ("wrong saved angular vector", "memcpy(body + 0x130 / 4, body + 0x410 / 4, 16);",
         "memcpy(body + 0x130 / 4, body + 0x420 / 4, 16);"),
        ("wrong saved point vector", "memcpy(body + 0x140 / 4, body + 0x420 / 4, 16);",
         "memcpy(body + 0x140 / 4, body + 0x410 / 4, 16);"),
        ("reverse origin correction", "body[0x110 / 4 + axis] += cross;", "body[0x110 / 4 + axis] -= cross;"),
        ("drop fused subtraction", "__builtin_fmaf(position[z], angular[y], -product)",
         "position[z] * angular[y] - product"),
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
                             Options(trials=800, seed=1, patches=((old, new),))).run()
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
