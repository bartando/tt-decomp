"""Behavioral mutation proofs for the remaining outcome-helper chain.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_prediction_outcome_helpers_mutations.py
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("ball_predict_mark_hittable_window", "void BallPredict_MarkHittableWindow(", [
        ("empty window", "    auto* state =", "    return;\n    auto* state ="),
        ("omit leading-contact skip", "while (data->At(from).bounced != 0) ++from;", "(void)from;"),
        ("include end index", "i < count;", "i <= count;"),
        ("allow radius equality", "sample.pos.y <= Radius()", "sample.pos.y < Radius()"),
        ("reject unordered height", "sample.pos.y <= Radius()", "!(sample.pos.y > Radius())"),
        ("ignore next contact", " || sample.bounced != 0", ""),
        ("write wrong hittable flag", "sample.hittable = 1;", "sample.hittable = 0;"),
    ]),
    ("ball_predict_mark_late_table_exit", "void BallPredict_MarkLateTableExit(", [
        ("empty late-exit classifier", "    gdBallPredictData* data =", "    return;\n    gdBallPredictData* data ="),
        ("subtract ball radius", "->height + Radius()", "->height - Radius()"),
        ("accept too-early low sample", "from + 2 >= i", "from + 1 >= i"),
        ("accept unordered height", "data->At(i).pos.y <= threshold", "!(data->At(i).pos.y > threshold)"),
        ("ignore hittability", "sample.hittable == 0 || ", ""),
        ("ignore contact flag", " || sample.bounced != 0", ""),
        ("include rectangle width equality", "__builtin_fabsf(sample.pos.x) < g_ballRecoveryHalfWidth", "__builtin_fabsf(sample.pos.x) <= g_ballRecoveryHalfWidth"),
        ("include rectangle length equality", "__builtin_fabsf(sample.pos.z) < g_ballRecoveryHalfLength", "__builtin_fabsf(sample.pos.z) <= g_ballRecoveryHalfLength"),
        ("ignore caller ID array", "auto** ids = static_cast<uint32_t**>(idsArray);", "auto** ids = &data->m_ids;"),
    ]),
    ("ball_predict_is_finite_xyz", "uint32_t BallPredict_IsFiniteXYZ(", [
        ("accept all vectors", "    const float* lanes =", "    return 1;\n    const float* lanes ="),
        ("reject finite vectors", "    return 1;", "    return 0;"),
        ("test ignored w lane", "i < 3", "i < 4"),
        ("omit z lane", "i < 3", "i < 2"),
        ("wrong exponent mask", "bits & 0x7F800000u", "bits & 0x7F000000u"),
    ]),
    ("ball_predict_forecast_outcome", "void BallPredict_ForecastOutcome(", [
        ("omit initial outcome reset", "    *result = 0;", "    (void)result;"),
        ("validate wrong position vector", "BallPredict_IsFiniteXYZ(&sample->pos)", "BallPredict_IsFiniteXYZ(&sample->angVel)"),
        ("validate wrong velocity vector", "BallPredict_IsFiniteXYZ(&sample->vel)", "BallPredict_IsFiniteXYZ(&sample->angVel)"),
        ("add ball radius", "->height - Radius()", "->height + Radius()"),
        ("invert bounce side", "sample->pos.z < 0.0f ? 2 : 1", "sample->pos.z > 0.0f ? 2 : 1"),
        ("ignore descending-velocity gate", "sample->vel.y < 0.0f", "true"),
        ("bounce overrides descending floor", "if (sample->bounced != 0) *result = sample->pos.z < 0.0f ? 2 : 1;", "if (sample->bounced != 0) { *result = sample->pos.z < 0.0f ? 2 : 1; break; }"),
        ("wrong step bank", "BallPredict_StepSample(sample, 1);", "BallPredict_StepSample(sample, 0);"),
        ("omit result check after step", "BallPredict_StepSample(sample, 1);\n        if (*result != 0) break;", "BallPredict_StepSample(sample, 1);"),
        ("run one extra step", "steps >= gdBallPredictData::kMaxSamples", "steps > gdBallPredictData::kMaxSamples"),
        ("wrong limit log argument", "samples!\", gdBallPredictData::kMaxSamples);", "samples!\", gdBallPredictData::kMaxSamples - 1);"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_prediction_outcome_helpers.cpp").read_text()
    count = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=800, seed=1,
                                     patches=((body, body.replace(old, new)),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: "
                  f"{output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            count += 1
    print(f"Caught {count}/{count} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
