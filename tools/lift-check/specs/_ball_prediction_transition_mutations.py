"""Reject broken cached-ring/state interpolation and transition blending.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_prediction_transition_mutations.py
Only behavioral FAIL (exit 1) counts; patches affect build-cache copies only.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

SOURCE = "src/game/ball/ball_prediction_stream.cpp"
CASES = [
    ("ball_predict_get_interpolated_sample", "gdBallPredictSample* BallPredict_GetInterpolatedSample(", [
        ("overwrite empty cache", "    int first = -1;", "    ring->cached.time = 0.0f;\n    int first = -1;"),
        ("return oldest sample", "return &ring->cached;", "return &ring->ring.At(0);"),
        ("wrong second sample", "&ring->ring.At(second), factor", "&ring->ring.At(first), factor"),
    ]),
    ("ball_predict_blend_transition_samples", "void BallPredict_BlendTransitionSamples(", [
        ("lose retained height", "out->pos.y = first->pos.y;", "out->pos.y = second->pos.y;"),
        ("overwrite untouched W", "    out->vel = first->vel;", "    out->pos.w = 0.0f;\n    out->vel = first->vel;"),
        ("skip horizontal interpolation", "out->pos.x = __builtin_fmaf(second->pos.x - first->pos.x, factor, first->pos.x);", "out->pos.x = first->pos.x;"),
        ("use second hittability", "first->hittable != 0 && first->bounced == 0;", "first->hittable != 0 && first->bounced == 0 && second->hittable != 0;"),
        ("wrong hemisphere", "dot < g_kFloatConst_D110", "dot > g_kFloatConst_D110"),
    ]),
    ("ball_predict_interpolate_state", "void BallPredict_InterpolateState(", [
        ("ignore low-byte gate", "static_cast<uint8_t>(BallPredict_ShouldUsePrevious(statePtr))", "BallPredict_ShouldUsePrevious(statePtr)"),
        ("wrong live bank", "state->banks[1]->m_samples", "state->banks[0]->m_samples"),
        ("wrong previous bank", "state->banks[0]->m_samples", "state->banks[1]->m_samples"),
        ("retain live cache reference", "gdBallPredictSample current;\n        CopySample(current, *BallPredict_GetInterpolatedSample(state->banks[1]->m_samples, nullptr, time));", "gdBallPredictSample& current = *BallPredict_GetInterpolatedSample(state->banks[1]->m_samples, nullptr, time);"),
        ("lose lower and unordered clamp", "raw >= 0.0f ? static_cast<double>(raw) : g_kDoubleConst_79B00", "static_cast<double>(raw)"),
        ("lose upper clamp", "lower - g_kDoubleConst_79B08 >= 0.0", "false"),
        ("divide blend rate", "* state->blendRate", "/ state->blendRate"),
        ("swap transition samples", "&current, &previous, factor", "&previous, &current, factor"),
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
