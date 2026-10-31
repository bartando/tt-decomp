"""Behavioral mutation proof for prediction refill and interpolation helpers.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_prediction_stream_mutations.py
Only behavioral FAIL (exit 1) counts. Patches are limited to cached build copies.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

SOURCE = "src/game/ball/ball_prediction_stream.cpp"
CASES = [
    ("ball_predict_advance_samples", "void BallPredict_AdvanceSamples(", [
        ("empty lift", "    const int popped =", "    return;\n    const int popped ="),
        ("repeat selected bank", "gdBallPredictData* live = state->banks[1];", "gdBallPredictData* live = state->banks[bank];"),
        ("append into full live bank", "live->m_count != gdBallPredictData::kMaxSamples", "true"),
        ("ignore completed prediction", "data->m_complete == 0", "true"),
        ("only refill one sample", "i < popped", "i < 1"),
        ("retain old state after sampler", "state = CurrentState();\n                state->banks", "state = state;\n                state->banks"),
        ("wrong exhaustion threshold", "data->m_count < 2", "data->m_count < 1"),
        ("lose bounce extension count", "data->ExtendBounceList(popped);", "data->ExtendBounceList(0);"),
    ]),
    ("ball_predict_flag9_crossing", "uint32_t BallPredict_HasFlag9Crossing(", [
        ("include oldest sample", "int i = 1", "int i = 0"),
        ("include previous frame boundary", "previous < sample.time", "previous <= sample.time"),
        ("exclude current frame boundary", "now >= sample.time &&", "now > sample.time &&"),
        ("wrong flag", "sample.flag9 != 0", "sample.bounced != 0"),
        ("continue past future sample", "if (!(now >= sample.time)) return false;", "if (false) return false;"),
    ]),
    ("ball_predict_find_neighbors", "bool BallPredict_FindNeighborIndices(", [
        ("succeed on empty ring", "        return false;", "        return true;"),
        ("wrong singleton factor", "*factor = g_kFloatConst_D110;", "*factor = g_kFloatConst_D108;"),
        ("wrong clipped endpoint", "*first = ring->count - 2;", "*first = ring->count - 1;"),
        ("wrong interpolation numerator", "time - ring->At(i).time", "time - ring->At(i + 1).time"),
        ("wrong second index", "*second = i + 1;", "*second = i;"),
    ]),
    ("ball_predict_blend_samples", "void BallPredict_BlendSamples(", [
        ("omit position w", "lane < 4", "lane < 3"),
        ("carry second velocity", "out->vel = first->vel;", "out->vel = second->vel;"),
        ("lose bounce flag", "out->bounced = first->bounced;", "out->bounced = 0;"),
        ("ignore second hittability", "second->hittable != 0 && second->bounced == 0", "true"),
        ("wrong hemisphere", "dot < g_kFloatConst_D110", "dot > g_kFloatConst_D110"),
        ("omit VMX single spill", "FlushPredictionVmx(vectorFactor)", "FlushPredictionVmx(factor)"),
    ]),
    ("ball_predict_interpolate_samples", "void BallPredict_InterpolateSamples(", [
        ("empty wrapper", "    int first = -1;", "    return;\n    int first = -1;"),
        ("wrong requested time", "&factor, time)", "&factor, 0.0f)"),
        ("wrong second sample", "&ring->At(second), factor", "&ring->At(first), factor"),
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
            assert old in body, f"missing anchor: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"), Options(
                    trials=128, seed=1, patches=((body, body.replace(old, new)),))).run()
            first_line = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: {first_line}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
