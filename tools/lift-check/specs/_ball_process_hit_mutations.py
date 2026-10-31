"""Proof the ProcessHit and shot-copy specs reject behavioral regressions.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_process_hit_mutations.py
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

SOURCE = "src/game/ball/ball_process_hit.cpp"
CASES = [
    ("ball_predict_copy_shot", "bpShot* ballPredict_CopyShot(", [
        ("empty copy", "    for (int i = 0; i < 3;", "    return dst;\n    for (int i = 0; i < 3;"),
        ("copy shot padding", "    dst->v10 = src->v10;", "    dst->_pad0C = src->_pad0C;\n    dst->v10 = src->v10;"),
        ("lose vector w lane", "    dst->v50 = src->v50;", "    dst->v50.x = src->v50.x;\n    dst->v50.y = src->v50.y;\n    dst->v50.z = src->v50.z;"),
        ("omit flags", "    dst->hB6 = src->hB6;", "    (void)src->hB6;"),
        ("wrong destination return", "    return dst;", "    return nullptr;"),
    ]),
    ("ball_process_hit", "void ballPredict_ProcessHit(", [
        ("empty lift", "    auto* hit =", "    return;\n    auto* hit ="),
        ("poll all bits", "static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr))", "io_Input_poll_9D68(g_input_obj_ptr)"),
        ("drop previous prediction", "state->predict->m_count > 1 && !live", "false && !live"),
        ("copy old secondary clock", "first.time2 = old.time;", "first.time2 = old.time2;"),
        ("omit ball counter", "    ball->counterC4 = 0;", "    (void)ball->counterC4;"),
        ("ignore pace clamp", "const double clamped = lower - 1.0 >= 0.0 ? 1.0 : lower;", "const double clamped = pace;"),
        ("wrong reciprocal rate", "state->samplePeriod = reciprocalRate * paceFactor;", "state->samplePeriod = reciprocalRate / paceFactor;"),
        ("omit first sample", "    state->predict->AddSample(&first);", "    (void)first;"),
        ("replay velocity instead of spin", "record.angVel = first.angVel;", "record.angVel = first.vel;"),
        ("wrong physics bank", "BallPredict_StepSample(&sample, 1);", "BallPredict_StepSample(&sample, 0);"),
        ("drop sample spin", "dst.angVel = sample.angVel;", "(void)sample.angVel;"),
        ("wrong ring wrap", "if (++data->m_head == gdBallPredictData::kMaxSamples)", "if (++data->m_head == gdBallPredictData::kMaxSamples - 1)"),
        ("expire one step early", "expiredSteps > 6", "expiredSteps >= 6"),
        ("require consecutive floor steps", "if (sample.pos.y <= radius) ++expiredSteps;",
         "if (sample.pos.y <= radius) ++expiredSteps; else expiredSteps = 0;"),
        ("count consecutive contacts", "if (previous.bounced == 0)", "if (true)"),
        ("omit completion flag", "state->predict->m_complete = 1;", "(void)state->predict->m_complete;"),
        ("omit launch spin adjustment", "if (!live) BallPredict_ApplyLaunchSpin", "if (false) BallPredict_ApplyLaunchSpin"),
        ("test all playback bits", "static_cast<uint8_t>(updateNow) != 0", "updateNow != 0"),
        ("publish wrong spin", "data->m_hitVel = outSpin;", "data->m_hitVel = outVelocity;"),
        ("publish wrong velocity", "state->predict->m_hitPos = outVelocity;", "state->predict->m_hitPos = outSpin;"),
        ("wrong message", "PostPageGroupMessageFmt(0x22, 0x40", "PostPageGroupMessageFmt(0x23, 0x40"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / SOURCE).read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=128, seed=1,
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
