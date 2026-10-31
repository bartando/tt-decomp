"""Behavioral mutation checks for the sampler; BUILD/SPEC never count as caught.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_ball_prediction_step_mutations.py
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("empty lift", "    using namespace predictionStep;", "    return;\n    using namespace predictionStep;"),
    ("wrong shot stride", "static_cast<uint32_t>(g_currentInputSlot) * 0x1A0u", "static_cast<uint32_t>(g_currentInputSlot) * 0x190u"),
    ("omit acceleration", "BallFlight_Acceleration(&acceleration, Shot(), &velocity, &spin);", "acceleration = {};"),
    ("truncate rate instead of round", "->frameRate + 0.5f;", "->frameRate;"),
    ("omit z direction stop", "if ((Bits(velocity.z) >> 31) != oldSign)", "if (false)"),
    ("omit sweep extension", "length = distance + 0.001f;", "length = distance;"),
    ("omit stationary fallback", "if (speedSq > 1e-12f)", "if (false)"),
    ("test only sweep start", "__builtin_fabsf(start.z) < limit || __builtin_fabsf(end.z) < limit", "__builtin_fabsf(start.z) < limit"),
    ("test only sweep end", "__builtin_fabsf(start.z) < limit || __builtin_fabsf(end.z) < limit", "__builtin_fabsf(end.z) < limit"),
    ("omit descending net adjustment", "if (sample->flag9 != 0 && axis.y < 0.0f &&", "if (false && axis.y < 0.0f &&"),
    ("test all sweep return bits", "static_cast<uint8_t>(collided) != 0", "collided != 0"),
    ("omit corner angle", "__builtin_fabsf(cornerAngle) > 1e-6f", "false"),
    ("omit elasticity friction override", "if (elasticity == 0.949999988079071f)", "if (false)"),
    ("classify wrong net surface", "if (hit.surface == 1)", "if (hit.surface == 2)"),
    ("omit contact position correction", "end = Nmsub(velocity, correction, end);", "(void)end;"),
    ("omit contact velocity correction", "velocity = Nmsub(acceleration, correction, velocity);", "(void)velocity;"),
    ("omit bounce", "BallFlight_Bounce(Shot(), &hit.normal, &end, &velocity, &spin, radius, friction, elasticity);", "(void)friction;"),
    ("omit contact-time clamp", "const double fraction = lower - 1.0 >= 0.0 ? 1.0 : lower;", "const double fraction = hit.fraction;"),
    ("omit spin writeback", "__builtin_memcpy(&sample->angVel, &spin, 16);", "(void)spin;"),
    ("omit table flag", "sample->bounced = static_cast<uint8_t>(tableBounce);", "sample->bounced = 0;"),
    ("omit net flag", "sample->flag9 = static_cast<uint8_t>(netBounce);", "sample->flag9 = 0;"),
    ("use wrong prediction bank", "CurrentState()->banks[bank]", "CurrentState()->banks[bank ^ 1]"),
    ("clear retained hittability", "if (previous.hittable != 0 && previous.bounced == 0) sample->hittable = 1;", "if (previous.hittable != 0 && previous.bounced == 0) sample->hittable = 1; else sample->hittable = 0;"),
    ("use real time for prediction clock", "sample->time += predictionStep;", "sample->time += step;"),
    ("use prediction time for real clock", "sample->time2 += step;", "sample->time2 += predictionStep;"),
    ("omit VMX flushing", "    uint32_t bits;\n    __builtin_memcpy(&bits, &value, 4);\n    if ((bits & 0x7F800000u) == 0)", "    return value;\n    uint32_t bits;\n    __builtin_memcpy(&bits, &value, 4);\n    if ((bits & 0x7F800000u) == 0)"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_prediction_step.cpp").read_text()
    for label, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("ball_prediction_step.py"),
                         Options(trials=256, seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
