"""Mutation proof for the local and remote creature velocity lifts.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_creature_velocity_link_mutations.py

Only cache copies are patched. A behavioral FAIL must kill every mutant;
BUILD, SPEC, UNSUPPORTED, crashes and surviving mutants fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

CASES = [
    ("pong_mover_compute_target_velocity", "src/game/creature/pong_creature.cpp",
     "float* pongMover_ComputeTargetVelocity(", [
        ("empty lift", "    alignas(16) float direction", "    return out;\n    alignas(16) float direction"),
        ("reverse target direction", "moverFlushVmx(target[lane]) - moverFlushVmx(origin[lane])", "moverFlushVmx(origin[lane]) - moverFlushVmx(target[lane])"),
        ("wrong separation axis", "__builtin_fabsf(target[0] - origin[0])", "__builtin_fabsf(target[2] - origin[2])"),
        ("omit time scaling", "distance / mover->m_posZ", "distance"),
        ("wrong short-range envelope", "1.4492753744125366f", "0.7246376872062683f"),
        ("omit envelope square", "weight = clamped * clamped", "weight = clamped"),
        ("omit absolute speed", "__builtin_fabsf(pongMover_GetInputSpeed(mover))", "pongMover_GetInputSpeed(mover)"),
        ("drop w", "lane < 4", "lane < 3"),
    ]),
    ("pong_mover_compute_local_velocity", "src/game/creature/pong_creature.cpp",
     "float* pongMover_ComputeLocalVelocity(", [
        ("empty lift", "    const auto* creature", "    return out;\n    const auto* creature"),
        ("wrong cached z", "out[2] = mover->m_unk34", "out[2] = mover->m_unk30"),
        ("skip unordered blend", "!(pongMover_GetBlendWeight(mover) <= 0.0f)", "pongMover_GetBlendWeight(mover) > 0.0f"),
        ("miss arrival equality", "distance <= mover->m_unk50", "distance < mover->m_unk50"),
        ("wrong arrival flag", "mover->m_flags |= 8", "mover->m_flags |= 4"),
        ("omit arrival w", "memset(out, 0, 16)", "memset(out, 0, 12)"),
        ("wrong target z", "mover->m_posY, 0.0f", "mover->m_posX, 0.0f"),
        ("omit saturation", "out[0] = clamp(velocity[0])", "out[0] = velocity[0]"),
    ]),
    ("pong_mover_compute_remote_velocity", "src/game/creature/pong_creature.cpp",
     "float* pongMover_ComputeRemoteVelocity(", [
        ("empty lift", "    out[0]", "    return out;\n    out[0]"),
        ("wrong special type", "type == 2", "type == 1"),
        ("reverse threshold flag", "!(mover->m_flags & 0x20)", "(mover->m_flags & 0x20)"),
        ("wrong arrival threshold", "mover->m_unk54", "mover->m_unk50"),
        ("wrong arrival flag", "mover->m_flags |= 8", "mover->m_flags |= 4"),
        ("ignore callback result", "memcpy(out, result, 16)", "memcpy(out, scratch, 16)"),
        ("drop callback w", "memcpy(out, result, 16)", "memcpy(out, result, 12)"),
        ("omit frame rate", "distance * frameRate", "distance"),
        ("omit speed limit", "if (speed > mover->m_unk48) speed = mover->m_unk48;", "(void)mover;"),
        ("omit normalization", "moverNormalize(direction)", "(void)direction"),
    ]),
    ("pong_mover_compute_target_velocity", "src/game/creature/pong_creature.cpp",
     "void moverNormalize(", [
        ("normalize w in dot", "lane < 3", "lane < 4"),
        ("omit normalization", "    double dot", "    return;\n    double dot"),
        ("use squared reciprocal", "correction + reciprocal", "correction + squared"),
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
