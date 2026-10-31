"""Mutation proof for the animation-pair ABI and virtual dispatch.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_locomotion_setup_animation_pair_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("locomotion_setup_animation_pair", "src/game/creature/pong_creature.cpp",
     "bool LocomotionStateAnim::SetupAnimationPair(", [
        ("empty lift", "    (void)unusedR6;", "    return false;\n    (void)unusedR6;"),
        ("use r6 instead of r7", "    (void)unusedR6;", "    param = unusedR6;"),
        ("truncate first ID", "FindAnimationByID(animID1, 0)", "FindAnimationByID(static_cast<uint16_t>(animID1), 0)"),
        ("truncate second ID", "FindAnimationByID(animID2, 0)", "FindAnimationByID(static_cast<uint16_t>(animID2), 0)"),
        ("wrong lookup ID", "FindAnimationByID(animID2, 0)", "FindAnimationByID(animID2, 1)"),
        ("skip second lookup on first miss", "    auto* second =", "    if (!first) return false;\n    auto* second ="),
        ("wrong first virtual", "first->SetVector(", "first->SetQuaternion("),
        ("wrong second virtual", "second->SetQuaternion(", "second->SetVector("),
        ("wrong translation offset", "*>(param) + 16", "*>(param) + 0"),
        ("wrong quaternion offset", "static_cast<const float*>(param)", "static_cast<const float*>(param) + 4"),
        ("wrong success result", "    return true;", "    return false;"),
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
