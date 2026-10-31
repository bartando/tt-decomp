"""Mutation checks for envelope membership and the reused prefix-sum lift.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_audio_envelope_mutations.py
Only a behavioral FAIL counts; compilation or invalid-fixture failures do not.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("audio_control_is_within_active_envelope", "src/game/ball/ball_audio_envelope.cpp",
     "bool AudioControl_IsWithinActiveEnvelope(", [
         ("empty lift", "    auto* bytes =", "    return false;\n    auto* bytes ="),
         ("invert active byte", "envelope->active == 0", "envelope->active != 0"),
         ("read active word", "envelope->active == 0", "*reinterpret_cast<const uint32_t*>(bytes + 0x24) == 0"),
         ("wrong duration object", "bytes + 0x2C", "bytes + 0x28"),
         ("wrong first prefix", "SumFloatArray(0)", "SumFloatArray(1)"),
         ("wrong final prefix", "SumFloatArray(4)", "SumFloatArray(3)"),
         ("include lower equality", "first < threshold", "first <= threshold"),
         ("exclude upper equality", "threshold <= durations->SumFloatArray(4)", "threshold < durations->SumFloatArray(4)"),
         ("accept unordered first comparison", "!(first < threshold)", "first >= threshold"),
         ("accept unordered final comparison", "threshold <= durations->SumFloatArray(4)", "!(threshold > durations->SumFloatArray(4))"),
     ]),
    ("audio_envelope_sum_float_array", "src/physics/ph_physics.cpp",
     "float rage::phBoundCapsule::SumFloatArray(", [
         ("empty sum", "    float sum =", "    return 0.0f;\n    float sum ="),
         ("wrong initial sum", "float sum = g_floatZero;", "float sum = 1.0f;"),
         ("wrong unrolled base", "this + 48", "this + 52"),
         ("wrong cleanup base", "remaining + 12", "remaining + 13"),
         ("skip final cleanup value", "if (remaining <= count)", "if (remaining < count)"),
         ("process extra chunk", "int chunks = total / 4;", "int chunks = total / 4 + 1;"),
         ("repeat unrolled element", "sum += ptr[2];", "sum += ptr[1];"),
         ("widen running sum", "float sum = g_floatZero;", "double sum = g_floatZero;"),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    count = 0
    for spec, path, signature, mutations in CASES:
        source = (root / path).read_text()
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
