"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_pcm_source_render_mutations.py

Only build-cache copies are mutated. Each case must produce behavioral FAIL
(exit 1); BUILD, SPEC, and UNSUPPORTED do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = [
    ("wrong output interface adjustment",
     "static_cast<uint8_t*>(output) - offsetof(AudioFrameBuffer, kind)",
     "static_cast<uint8_t*>(output) - (offsetof(AudioFrameBuffer, kind) - 4)"),
    ("discard output channels", "frame.channels = self->channels;", "frame.channels = 0;"),
    ("swallow resize failure", "return result;", "return 0;"),
    ("wrong inactive return", "return 1;", "return 0;"),
    ("render an ended source",
     "if (!(self->flags & 1) || (self->flags & 16))", "if (!(self->flags & 1))"),
    ("lose reset gain", "stream.gain = self->gain;", "stream.gain = 0.0f;"),
    ("leave filter history dirty",
     "for (auto& value : stream.filterHistory) value = 0;",
     "stream.filterHistory[0] = 0;"),
    ("saturate wrapping fade counter", "--self->fadeTicks;",
     "if (self->fadeTicks) --self->fadeTicks;"),
    ("decrement infinite loop count",
     "if (buffer->loopCount != UINT32_MAX) --buffer->loopCount;", "--buffer->loopCount;"),
    ("never decrement finite loops",
     "if (buffer->loopCount != UINT32_MAX) --buffer->loopCount;", "/* no decrement */"),
    ("restart loop at zero", "self->position = buffer->loopStart;", "self->position = 0;"),
    ("swap loop callback payload",
     "PcmSourceEvent event{self->context, buffer->context, 0};",
     "PcmSourceEvent event{buffer->context, self->context, 0};"),
    ("hold global lock across DSP and callbacks",
     "xaudioReleaseLock(g_xaudioSourceLock);\n\n    PcmSourceBuffer* buffer",
     "/* lock incorrectly held */\n\n    PcmSourceBuffer* buffer"),
    ("skip callbacks at exact output boundary", "for (;;) {",
     "for (;;) {\n        if (stream.outputFrames == stream.outputOffset) break;"),
    ("wrong completion argument",
     "(&self->sourceVtable, buffer, 0);", "(&self->sourceVtable, buffer, 1);"),
    ("keep freed buffer after completion",
     "buffer = nullptr; // callback may have unlinked/freed this buffer",
     "/* retain freed buffer */"),
    ("ignore loop region endpoint",
     "buffer->loopCount ? buffer->loopStart + buffer->loopFrames : buffer->frames",
     "buffer->frames"),
    ("fail to clamp starting input position",
     "self->position < end ? self->position : end", "self->position"),
    ("lose buffer position accounting", "self->position += processed;", "self->position = processed;"),
    ("lose cumulative samples", "self->samplesPlayed += processed;", "self->samplesPlayed = processed;"),
    ("wrong silence channel stride", "stream.output + stream.outputOffset + channel * 256",
     "stream.output + stream.outputOffset + channel * 255"),
    ("omit final gain commit",
     "xaudioAcquireLock(g_xaudioSourceLock);\n    stream.previousGain = stream.gain;",
     "xaudioAcquireLock(g_xaudioSourceLock);\n    /* missing gain commit */"),
    ("mark a nonempty queue ended",
     "if (!firstBuffer()) setFlags(16, 16);", "if (firstBuffer()) setFlags(16, 16);"),
    ("never stop underrunning source", "} else {\n            stop();",
     "} else {\n            /* missing stop */"),
    ("ignore ended fade stop condition",
     "self->fadeTicks == 0 || (self->flags & 16)", "self->fadeTicks == 0"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / SOURCE).read_text()
    start = source.index("int32_t PcmSource_Render(")
    target = source[start:source.index("\n}", start) + 2]
    spec = Path(__file__).with_name("pcm_source_render.py")
    for name, old, new in MUTATIONS:
        assert target.count(old) == 1, f"mutation anchor changed: {name}"
        mutated = target.replace(old, new, 1)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((target, mutated),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


SOURCE = "src/rage/audio/xma_source.cpp"

if __name__ == "__main__":
    raise SystemExit(main())
