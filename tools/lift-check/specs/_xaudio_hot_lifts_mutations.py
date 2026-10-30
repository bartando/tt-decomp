"""Mutation proof for both hot SDK audio lifts. Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_xaudio_hot_lifts_mutations.py

Patches only build-cache copies. Only behavioral FAIL (exit 1) counts; build,
spec or unsupported errors are not accepted as a caught mutation.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


DECODER = [
    ("wrong already-locked return",
     "if (self->flags & 0x20000) return 1;", "if (self->flags & 0x20000) return 0;"),
    ("skip the locked fast path",
     "if (self->flags & 0x20000) return 1;", "if (false) return 1;"),
    ("read MMIO in native byte order",
     "((raw >> 24) | ((raw >> 8) & 0xff00)\n                       | ((raw << 8) & 0xff0000) | (raw << 24)) ^ 0x200",
     "raw ^ 0x200"),
    ("omit hardware context toggle",
     "| (raw << 24)) ^ 0x200;", "| (raw << 24));"),
    ("truncate hardware context ID",
     "contextId == current", "contextId == static_cast<uint16_t>(current)"),
    ("snapshot even when a context is busy",
     "if (self->contexts[i].contextId == current) return 0;", "if (false) return 0;"),
    ("check only the first busy context",
     "if (self->contexts[i].contextId == current) return 0;",
     "if (i == 0 && self->contexts[i].contextId == current) return 0;"),
    ("copy only two snapshot vectors",
     "std::memcpy(context.words, context.hardware, 48);", "std::memcpy(context.words, context.hardware, 32);"),
    ("swap input validity bits",
     "(context.words[0] >> 20) & 3", "(context.words[0] >> 21) & 3"),
    ("leave consumed input identity",
     "context.input[0] = nullptr;", "/* stale first input identity */"),
    ("clear too much input configuration",
     "context.words[1] &= 0xfffff000;", "context.words[1] &= 0xffff0000;"),
    ("leave consumed byte count",
     "context.words[6] = 0;", "/* stale second input byte count */"),
    ("clear output validity while input remains",
     "if (validInputs == 0) context.words[4] &= 0x7fffffff;", "context.words[4] &= 0x7fffffff;"),
    ("omit snapshot lock flag",
     "self->flags |= 0x20000;", "/* snapshot not marked locked */"),
]

RESAMPLER = [
    ("leave previous gain stale",
     "stream->previousGain = stream->gain;", "/* previous gain not advanced */"),
    ("ramp one sample too slowly",
     "/ static_cast<float>(frames);", "/ static_cast<float>(frames + 1);"),
    ("wrong fixed-point rate scale",
     "(double(rate) - wholeStep) * 4294967296.0", "(double(rate) - wholeStep) * 2147483648.0"),
    ("discard initial fractional position",
     "uint64_t position = (uint64_t(wholePosition) << 32) | fractionalPosition;",
     "uint64_t position = (uint64_t(wholePosition) << 32);"),
    ("read PCM16 as unsigned",
     "static_cast<float>(cursor[index * 2])", "static_cast<float>(static_cast<uint16_t>(cursor[index * 2]))"),
    ("wrong PCM normalization",
     "float a = static_cast<float>(cursor[index * 2]) * 0x1p-15f;",
     "float a = static_cast<float>(cursor[index * 2]) * 0x1p-14f;"),
    ("replace lookahead by current sample",
     "cursor[index * 2 + 2]", "cursor[index * 2]"),
    ("read the wrong right-channel sample",
     "cursor[index * 2 + 3]", "cursor[index * 2 + 2]"),
    ("omit gain on interpolated delta",
     "float weightedBlend = xaudioVmxMultiply(blend, gains[lane]);", "float weightedBlend = blend;"),
    ("use a constant gain after first block",
     "gains[lane] = xaudioVmxAdd(gains[lane], blockGainStep);", "/* ramp not advanced */"),
    ("wrong planar channel stride",
     "destination[lane + 256] = right[lane];", "destination[lane + 128] = right[lane];"),
    ("forget to rebase fixed-point position",
     "position = static_cast<uint32_t>(position);", "/* integer position counted twice */"),
    ("omit input counter clamp",
     "stream->inputOffset = consumed < stream->inputFrames ? consumed : stream->inputFrames;",
     "stream->inputOffset = consumed;"),
    ("omit output counter clamp",
     "stream->outputOffset = produced < stream->outputFrames ? produced : stream->outputFrames;",
     "stream->outputOffset = produced;"),
    ("keep subnormal VMX operands and results",
     "if ((bits & 0x7f800000) == 0) bits &= 0x80000000;",
     "/* subnormals incorrectly preserved */"),
    ("lose fractional phase for next invocation",
     "stream->resamplePosition = static_cast<float>(XAudio_UInt64ToDouble(position) * 0x1p-32);",
     "stream->resamplePosition = static_cast<float>(XAudio_UInt64ToDouble(position) * 0x1p-31);"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/audio/xma_source.cpp").read_text()
    total = 0
    for name, mutations in [("xma_decoder_try_complete_lock", DECODER),
                            ("xaudio_resample_stereo16_ramp", RESAMPLER)]:
        for label, old, new in mutations:
            assert source.count(old) == 1, f"mutation anchor changed: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(name + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        total += len(mutations)
        print(f"{name}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
