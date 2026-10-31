"""Mutation proof for the creature court-braking lifts.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_creature_braking_link_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("pong_mover_get_movement_rate", "src/game/creature/pong_creature.cpp",
     "float pongMover_GetMovementRate(", [
        ("empty lift", "    const auto movementData", "    return 0.0f;\n    const auto movementData"),
        ("wrong latch byte", "mover->m_bHasTarget", "mover->m_bIsMoving"),
        ("wrong match stride", "index * 36", "index * 32"),
        ("wrong target rate", "movementData() + 0x5C", "movementData() + 0x60"),
        ("fold NaN interpolation", "const float delta = rate - rate;", "const float delta = 0.0f;"),
        ("wrong character rate", "movement + 0x6C", "movement + 0x64"),
        ("omit character rate", "return scale *", "return 1.0f *"),
     ]),
    ("pong_mover_adjust_velocity", "src/game/creature/pong_creature.cpp",
     "void pongMover_AdjustVelocity(", [
        ("empty lift", "    alignas(16) float lower", "    return;\n    alignas(16) float lower"),
        ("wrong side", "mover->m_creatureIndex, lower, upper", "0, lower, upper"),
        ("wrong position row", "instance + 0x40", "instance + 0x30"),
        ("wrong braking factor", "(distance * rate) * 2.0f", "(distance * rate) * 1.0f"),
        ("omit distance magnitude", "__builtin_fabsf(coordinate - low)", "coordinate - low"),
        ("reverse negative limit", "limit = -static_cast<float>", "limit = static_cast<float>"),
        ("wrong z component", "adjust(z, position[2], lower[2], upper[2]);", "adjust(z, position[1], lower[1], upper[1]);"),
        ("omit second axis", "adjust(z, position[2], lower[2], upper[2]);", "(void)z;"),
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
