"""Mutate caller argument wiring and pointer reloads in cache copies only."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "src/physics/ph_physics.cpp"
CASES = {
    "ph_articulated_set_timestep": [
        ("old argument order", "phArticulatedCollider_60F8(jointData, linearLimit, angularLimit, timestep);",
         "phArticulatedCollider_60F8(jointData, timestep, angularLimit, linearLimit);"),
        ("drop integration timestep", "ph_IntegrateJointPositions(jointData, timestep);",
         "ph_IntegrateJointPositions(jointData, 1.0f);"),
        ("reuse prepared pointer", "phArticulatedCollider_RestoreVelocities(reinterpret_cast<void*>(uintptr_t(self[0x1D0 / 4])));",
         "phArticulatedCollider_RestoreVelocities(jointData);"),
    ],
    "ph_articulated_post_integrate": [
        ("drop post-integration timestep",
         "ph_IntegrateJointPositions(reinterpret_cast<void*>(uintptr_t(self[0x1D0 / 4])), timestep);",
         "ph_IntegrateJointPositions(reinterpret_cast<void*>(uintptr_t(self[0x1D0 / 4])), 1.0f);"),
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
                             Options(trials=400, seed=1, patches=((old, new),))).run()
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
