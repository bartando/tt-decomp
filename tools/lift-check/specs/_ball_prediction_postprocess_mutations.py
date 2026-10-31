"""Behavioral mutation proof for launch-speed timing and hit-ID reset.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_prediction_postprocess_mutations.py
Only behavioral FAIL counts; repository sources remain untouched.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/game/ball/ball_prediction_postprocess.cpp"
CASES = [
    ("ball_predict_retime_launch_velocity", "void BallPredict_RetimeSamplesForLaunchVelocity(", [
        ("empty lift", "    const bpVec4 requested", "    return;\n    const bpVec4 requested"),
        ("invert speed gate", "requestedSquare < Dot3", "requestedSquare > Dot3"),
        ("wrong live bank", "->prediction;", "->prediction; prediction = *reinterpret_cast<gdBallPredictData**>(static_cast<uint8_t*>(g_game_state_ptr) + 0x10);"),
        ("include first interval", "int i = 2", "int i = 1"),
        ("shift easing start", "i - 2", "i - 1"),
        ("omit sine easing", "static_cast<float>(crt_sin(factor * 1.5707963705062866f))", "factor"),
        ("drop completed easing", ": 1.0f)", ": 0.0f)"),
        ("wrong clock", "current.time = previous.time + duration;", "current.time2 = previous.time + duration;"),
        ("lose cumulative timing", "current.time = previous.time + duration;", "current.time = originalPreviousTime + duration;"),
        ("include homogeneous lane", "Dot3(requested);", "Dot3(bpVec4{requested.x, requested.y, requested.w, requested.z});"),
    ]),
    ("ball_predict_reset_hit_ids", "void BallPredict_ResetHitIds(", [
        ("empty reset", "    auto* prediction", "    return;\n    auto* prediction"),
        ("leave final ID", "i < prediction->m_idCount", "i + 1 < prediction->m_idCount"),
        ("wrong reset time", "m_idTime = -1.0f", "m_idTime = 0.0f"),
        ("wrong classification bank", "BallPredict_BuildHitIds(1)", "BallPredict_BuildHitIds(0)"),
        ("skip recovery", "if ((prediction->m_ids[0] & 1) == 0) BallPredict_RecoverHitIds(1);", "(void)prediction;"),
        ("wrong completion flag", "(ids[0] & 1) == 0", "(ids[0] & 2) == 0"),
        ("lose cached ID owner", "ids[0] |= 1;", "prediction->m_ids[0] |= 1;"),
        ("retain stale ID owner", "prediction->m_ids[0] |= 2;", "ids[0] |= 2;"),
        ("omit fallback timestamp", "prediction->m_idTime = static_cast<PredictionClock*>(g_pongMatchTiming)->now;", "(void)prediction;"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / SOURCE).read_text()
    total = 0
    for spec, signature, mutants in CASES:
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutants:
            assert old in body, f"missing anchor {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"), Options(
                    trials=256, seed=1, patches=((body, body.replace(old,new)),))).run()
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
