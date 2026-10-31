"""Mutation proof for the recovered creature rotation callees.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_creature_rotation_link_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("creature_clamp_rotation_calls", "src/game/creature/pong_creature.cpp",
     "void LocomotionStateAnim_8110_g(", [
        ("empty lift", "    alignas(16) float matrix", "    return;\n    alignas(16) float matrix"),
        ("wrong clamp axis", "vec[1], minVec[1], maxVec[1]", "vec[0], minVec[1], maxVec[1]"),
        ("reverse bounds", "vec[2], minVec[2], maxVec[2]", "vec[2], maxVec[2], minVec[2]"),
        ("skip Euler rebuild", "    rage::mat33FromEuler(matrix, vec);", "    (void)vec;"),
        ("omit quaternion result", "    LocomotionStateAnim_B218_g(static_cast<float*>(quat), matrix);", "    (void)quat;"),
     ]),
    ("rage_mat33_from_euler", "src/rage/math/mat33.cpp", "void mat33FromEuler(", [
        ("empty recovered lift", "    float sx", "    return;\n    float sx"),
        ("wrong Euler axis", "cosSin(&cz, &sz, angles[2])", "cosSin(&cz, &sz, angles[1])"),
     ]),
    ("locomotion_state_anim_b218", "src/anim/locomotion.cpp", "void LocomotionStateAnim_B218_g(", [
        ("empty recovered lift", "    const float xx", "    return;\n    const float xx"),
        ("wrong quaternion scale", "0.25f / dominant", "0.5f / dominant"),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        # Skip declarations: each definition begins at column zero.
        start = source.index("\n" + signature) + 1
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec + ".py"),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f"MISSED {spec}: {label}: BUILD {exc}", flush=True)
                return 1
            report = output.getvalue()
            caught = rc == 1 and "faulted" not in report
            first = report.splitlines()[0] if report else "no checker output"
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(report)
                return 1
        total += len(mutations)
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
