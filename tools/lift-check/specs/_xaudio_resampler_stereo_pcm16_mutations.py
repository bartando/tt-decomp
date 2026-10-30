"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_xaudio_resampler_stereo_pcm16_mutations.py

Only behavioral FAIL (exit 1) counts; BUILD/SPEC/UNSUPPORTED do not. Patches
affect build-cache copies, leaving the real lift intact. Uses the spec's default
trial count and seed 1; each mutant stops at its first divergence.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = [
    ("wrong stereo input stride", "const int16_t* first = input + index * 2;",
     "const int16_t* first = input + index;"),
    ("wrong right output plane stride",
     "state->output[outputIndex + 256] = resampleInterpolate(\n            float(first[1])",
     "state->output[outputIndex + 255] = resampleInterpolate(\n            float(first[1])"),
    ("wrong PCM normalization",
     "float(first[0]) * 0x1p-15f, float(second[0]) * 0x1p-15f",
     "float(first[0]) * 0x1p-14f, float(second[0]) * 0x1p-14f"),
    ("omit history interpolation", "while (phase < 0 && remaining > 0)",
     "while (false && remaining > 0)"),
    ("lose inter-word fraction carry", "(low >> 1) | (low << 31)", "low >> 1"),
    ("round negative integer phase like division",
     "int64_t index = (phase >> 32) + (phase < 0 ? 1 : 0);", "int64_t index = phase / ONE;"),
    ("omit gain ramp", "float gainStep = resampleMultiply(difference, reciprocal);",
     "float gainStep = 0.0f;"),
    ("wrong ramp denominator", "1.0f / static_cast<float>(remaining)",
     "1.0f / static_cast<float>(remaining + 1)"),
    ("force endpoint gain instead of accumulated gain", "state->currentGain = gain;",
     "state->currentGain = state->targetGain;"),
    ("omit last left sample history", "state->history[0] = float(input[last * 2]) * 0x1p-15f;",
     "state->history[0] = 0.0f;"),
    ("update history even when output is full", "if (remaining != 0) {", "if (true) {"),
    ("do not consume final history sample", "            ++index;", "            /* omitted ++index */"),
    ("lose overshoot correction", "phase += (index - available) * ONE;",
     "/* omitted overshoot correction */"),
    ("lose fractional phase commit", "state->phase = static_cast<float>(double(phase) * 0x1p-32);",
     "state->phase = 0.0f;"),
    ("omit VMX denormal flush", "if ((bits & 0x7f800000u) == 0) bits &= 0x80000000u;",
     "/* omitted VMX flush */"),
    ("reverse interpolation endpoints",
     "float(first[0]) * 0x1p-15f, float(second[0]) * 0x1p-15f",
     "float(second[0]) * 0x1p-15f, float(first[0]) * 0x1p-15f"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/audio/xaudio_resampler.cpp").read_text()
    spec = Path(__file__).with_name("xaudio_resampler_stereo_pcm16.py")
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        lines = output.getvalue().splitlines()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {lines[0] if lines else '(no output)'}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
