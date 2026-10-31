"""Only behavioral FAIL counts as detecting a broken hit-ID lift.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_prediction_hit_ids_mutations.py
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("ball_prediction_build_hit_ids", "void BallPredict_BuildHitIds(", [
        ("empty lift", "    State* state =", "    return;\n    State* state ="),
        ("opposite starting side", "data->At(0).pos.z > 0.0f", "data->At(0).pos.z < 0.0f"),
        ("wrong shot stride", "* 0x1A0u;", "* 0x190u;"),
        ("wrong serve flag", "shotFlags & 0x1000", "shotFlags & 0x100"),
        ("serve net starts late", "BallPredict_FindNetContact(data, 0)", "BallPredict_FindNetContact(data, 1)"),
        ("omit net failure bit", "data->m_ids[0] |= 8;", "data->m_ids[0] |= 4;"),
        ("wrong serve bounce side", "BallPredict_FindBounceOnSide(data, positiveSide == 0, 0)", "BallPredict_FindBounceOnSide(data, positiveSide, 0)"),
        ("wrong fallback result class", "found == -1 || found == -3", "found == -1"),
        ("start bounce search too early", "const int from = found + 1;", "const int from = found;"),
        ("mark wrong window start", "state, 1, found + 1, originalCount, 1", "state, 1, found, originalCount, 1"),
        ("lose cached original count", "state, 1, found + 1, originalCount, 1", "state, 1, found + 1, data->m_count, 1"),
        ("wrong second fallback side", "BallPredict_FindBounceOnSide(data, positiveSide == 0, from)", "BallPredict_FindBounceOnSide(data, positiveSide, from)"),
        ("omit positive net-index gate", "if (net > 0 &&", "if (net >= 0 &&"),
    ]),
    ("ball_prediction_recover_hit_ids", "void BallPredict_RecoverHitIds(", [
        ("empty lift", "    gdBallPredictData* data =", "    return;\n    gdBallPredictData* data ="),
        ("treat sample zero as later hit", "if (first > 0)", "if (first >= 0)"),
        ("wrong end-search start", "FindFirstUnhittableFrom(first + 1)", "FindFirstUnhittableFrom(first + 2)"),
        ("wrong bounce classification", "if (data->At(end).bounced != 0)", "if (data->At(end).bounced == 0)"),
        ("wrong initial side", "data->At(first).pos.z < 0.0f", "data->At(first).pos.z > 0.0f"),
        ("test all forecast bits", "static_cast<uint8_t>(needsForecast) == 0", "needsForecast == 0"),
        ("wrong late-exit index", "BallPredict_MarkLateTableExit(1, &data->m_ids, first);", "BallPredict_MarkLateTableExit(1, &data->m_ids, first + 1);"),
        ("forecast first sample", "data->At(data->m_count - 1)", "data->At(0)"),
        ("omit forecast bank", "BallPredict_ForecastOutcome(&forecast, &outcome, 1);", "BallPredict_ForecastOutcome(&forecast, &outcome, 0);"),
        ("use forecast time for known hit", "data->m_idTime = data->At(first).time;", "data->m_idTime = forecast.time;"),
        ("omit table outcome bit", "case 1: case 2:", "case 1:"),
        ("include width boundary", "__builtin_fabsf(forecast.pos.x) < g_ballRecoveryHalfWidth", "__builtin_fabsf(forecast.pos.x) <= g_ballRecoveryHalfWidth"),
        ("include length boundary", "__builtin_fabsf(forecast.pos.z) < g_ballRecoveryHalfLength", "__builtin_fabsf(forecast.pos.z) <= g_ballRecoveryHalfLength"),
        ("select current player's input side", "const uint32_t opponent = g_currentInputSlot == 0;", "const uint32_t opponent = g_currentInputSlot != 0;"),
        ("invert input side", "[0x40 + opponent] == 0", "[0x40 + opponent] != 0"),
        ("drop forecast-zero early return", "if (outcome == 0) return;", "if (outcome == 12345) return;"),
        ("invert outcome one", "otherSide = negativeSide != 0;", "otherSide = negativeSide == 0;"),
        ("invert outcome two", "otherSide = negativeSide == 0;", "otherSide = negativeSide != 0;"),
        ("use wall clock for forecast result", "data->m_idTime = forecast.time;", "data->m_idTime = Now();"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_prediction_hit_ids.cpp").read_text()
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
                             Options(trials=512, seed=1,
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
