"""Mutation proof for playback and its recovered bank/physics predicates.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_playback_mutations.py
Only behavioral FAIL counts; repository sources remain untouched.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/game/ball/ball_playback.cpp"
CASES = [
    ("ball_predict_should_use_previous", "uint32_t BallPredict_ShouldUsePrevious(", [
        ("wrong receiver clock", "state->hitTime", "state->blendDuration"),
        ("wrong ring slot", "m_tail + 2", "m_tail + 1"),
        ("include equality", "sampleTime - state->hitTime < state->previousWindow", "sampleTime - state->hitTime <= state->previousWindow"),
    ]),
    ("ball_physics_queue_inactive", "bool BallPhysics_QueueInactive(", [
        ("skip queue", "    auto* sim =", "    return false;\n    auto* sim ="),
        ("accept full queue", "sim->count >= 120", "sim->count > 120"),
        ("wrong state mask", "& 7", "& 3"),
        ("wrong queued handle", "= handle;", "= 0;"),
        ("omit queue count", "++sim->count;", "(void)sim;"),
    ]),
    ("ball_prediction_playback", "void pg_70C8_g() {", [
        ("empty playback", "    using namespace ballPlayback;", "    return;\n    using namespace ballPlayback;"),
        ("lose flag low-byte check", "static_cast<uint8_t>(BallPredict_HasFlag9Crossing(prediction))", "BallPredict_HasFlag9Crossing(prediction)"),
        ("lose bank predicate low-byte check", "static_cast<uint8_t>(BallPredict_ShouldUsePrevious(state))", "BallPredict_ShouldUsePrevious(state)"),
        ("omit previous bank", "BallPredict_AdvanceSamples(0, false);", "(void)state;"),
        ("wrong descending message", "pg_E6E0(11, 0x40", "pg_E6E0(12, 0x40"),
        ("wrong table crossing axis", "previous.pos.z) < halfLength", "previous.pos.x) < halfLength"),
        ("omit launch position", "matrix.d = sample.pos;", "matrix.d = sample.vel;"),
        ("omit angular velocity", "instance->angularVelocity = spin;", "instance->angularVelocity = bpVec4{};"),
        ("lose old angular velocity", "instance->previousAngularVelocity = instance->angularVelocity;", "instance->previousAngularVelocity = spin;"),
        ("lose old transform", "instance->previousMatrix = instance->matrix;", "instance->previousMatrix = matrix;"),
        ("omit level sync", "static_cast<Level*>(g_pPhysicsLevel)->UpdateTransform(instance->levelIndex);", "(void)instance;"),
        ("wrong bounce message", "localBounce ? 1 : 2", "localBounce ? 2 : 1"),
        ("wrong impact scaling", "impulse * impactScale", "impulse"),
        ("omit paired net event", "pg_E6E0(44, 0x40, 0, 0);", "(void)instance;"),
        ("wrong player bit", "(1u << playerSide) | 0x40", "1u | 0x40"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / SOURCE).read_text()
    total = 0
    for spec, signature, mutants in CASES:
        start = source.index(signature)
        while source.find(";", start) < source.find("{", start):
            start = source.index(signature, start + len(signature))
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutants:
            assert old in body, f"missing anchor {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=256, seed=1,
                                     patches=((body, body.replace(old, new)),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
