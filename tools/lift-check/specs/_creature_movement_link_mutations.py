"""Mutation proof for the creature movement linker repairs.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_creature_movement_link_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

SOURCE = "src/game/creature/pong_creature.cpp"
# Per-spec source overrides for lifts that moved out of pong_creature.cpp.
SOURCES = {"pong_mover_get_input_speed": "src/game/creature/mover_input_speed.cpp"}
CASES = [
    ("pong_mover_get_blend_weight", "float pongMover_GetBlendWeight(", [
        ("empty result", "return (mover->m_flags & 0x12) ? 1.0f : mover->m_unk1C;", "return 0.0f;"),
        ("omit timed override", "& 0x12", "& 0x10"),
        ("omit remote override", "& 0x12", "& 0x02"),
        ("wrong weight field", "mover->m_unk1C", "mover->m_unk20"),
    ]),
    ("pong_mover_get_input_speed", "float pongMover_GetInputSpeed(", [
        ("empty result", "    if (mover->m_flags & 4)", "    return 0.0f;\n    if (mover->m_flags & 4)"),
        ("wrong override bit", "m_flags & 4", "m_flags & 2"),
        ("wrong override speed", "0x14), 0x64)", "0x14), 0x60)"),
        ("wrong match slot stride", "slot * 36", "slot * 32"),
        ("wrong character scale", "0x28), 0x64)", "0x28), 0x60)"),
        ("omit scale", "return scale *", "return 1.0f *"),
    ]),
    ("pong_mover_update_movement_state", "void pongMover_UpdateMovementState(", [
        ("empty lift", "    if (__builtin_fabsf", "    return;\n    if (__builtin_fabsf"),
        ("ignore second input axis", "__builtin_fabsf(mover->m_unk24) == 0.0f", "true"),
        ("expire stop equality", "m_targetTimer > g_moverStopDelay", "m_targetTimer >= g_moverStopDelay"),
        ("expire unordered stop timer", "mover->m_targetTimer > g_moverStopDelay", "!(mover->m_targetTimer <= g_moverStopDelay)"),
        ("omit stop timer tick", "m_targetTimer += g_kTransitionStep", "m_targetTimer += 0.0f"),
        ("omit move timer tick", "m_moveTimer += g_kTransitionStep", "m_moveTimer += 0.0f"),
        ("miss start equality", "m_moveTimer >= g_moverStartDelay", "m_moveTimer > g_moverStartDelay"),
        ("expire unordered move timer", "mover->m_moveTimer >= g_moverStartDelay", "!(mover->m_moveTimer < g_moverStartDelay)"),
        ("miss z sign reversal", "mover->m_unk2C * mover->m_unk24 < 0.0f", "false"),
        ("retain target latch", "        mover->m_bHasTarget = 0;\n        mover->m_bIsMoving", "        mover->m_bHasTarget = 1;\n        mover->m_bIsMoving"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, signature, mutations in CASES:
        source = (root / SOURCES.get(spec, SOURCE)).read_text()
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
