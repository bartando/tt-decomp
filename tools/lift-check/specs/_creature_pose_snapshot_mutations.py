"""Mutation proof for the compensated creature pose snapshots.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_creature_pose_snapshot_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("creature_copy_compensated_pose", "src/game/creature/creature_pose.cpp",
     'extern "C" void LocomotionState_CD70_g(', [
        ("empty lift", "    const auto* bytes", "    return;\n    const auto* bytes"),
        ("wrong bank stride", "banks[bank * 2]", "banks[bank]"),
        ("walk bones forward", "for (int bone = count - 1; bone >= 0; --bone)", "for (int bone = 0; bone < count; ++bone)"),
        ("wrong bind stride", "bone * 0xC0", "bone * 0x80"),
        ("wrong rest offset", "+ 0x50;", "+ 0x40;"),
        ("omit third rotation row", "row < 3", "row < 2"),
        ("wrong y column", "poseDot3(restPosition, matrix, 1)", "poseDot3(restPosition, matrix, 2)"),
        ("wrong translation w", "offsets[4] = {x, y, z, x}", "offsets[4] = {x, y, z, 0.0f}"),
        ("omit translation w", "lane < 4", "lane < 3"),
        ("reverse compensation", "flushPoseFloat(translation[lane]) - offsets[lane]", "offsets[lane] - flushPoseFloat(translation[lane])"),
    ]),
    ("creature_copy_compensated_pose", "src/game/creature/creature_pose.cpp",
     "float poseDot3(", [
        ("round dot each step", "double sum = 0.0", "float sum = 0.0f"),
        ("include rest w", "axis < 3", "axis < 4"),
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
            assert body.count(old) >= 1, f"mutation anchor changed: {spec}: {label}"
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
