"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_xma_source_submit_buffers_mutations.py

Mutates build-cache copies only. Each case must fail behaviorally (exit 1);
BUILD, SPEC and UNSUPPORTED errors do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = [
    ("wrong full-slot return",
     "if (!XmaDecoder_HasInputSpace(self->decoder, i)) return 1;",
     "if (!XmaDecoder_HasInputSpace(self->decoder, i)) return 0;"),
    ("wrong completion status bit",
     "&& !(XmaDecoder_GetStreamStatus(self->decoder, i) & 8)) {",
     "&& !(XmaDecoder_GetStreamStatus(self->decoder, i) & 4)) {"),
    ("complete a buffer still pending on another stream",
     "pending = true;\n                    break;",
     "pending = false;\n                    break;"),
    ("retire the final playing buffer",
     "buffer->state == 4 && (next || !(self->flags & 1) || (self->flags & 16))",
     "buffer->state == 4"),
    ("hold the source lock across completion",
     "xaudioReleaseLock(self->lock);\n            using CompleteFn",
     "/* source lock incorrectly held */\n            using CompleteFn"),
    ("hold the global lock across completion",
     "xaudioReleaseLock(g_xaudioSourceLock);\n            xaudioReleaseLock(self->lock);\n            using CompleteFn",
     "/* global lock incorrectly held */\n            xaudioReleaseLock(self->lock);\n            using CompleteFn"),
    ("read next after the callback frees current",
     "buffer = next;\n    }\n    xaudioReleaseLock(g_xaudioSourceLock);",
     "buffer = nextBuffer(self, buffer);\n    }\n    xaudioReleaseLock(g_xaudioSourceLock);"),
    ("continue queue after input slots fill",
     "if (!space) break;", "if (false) break;"),
    ("stop midway through a multistream buffer",
     "if (!XmaDecoder_HasInputSpace(self->decoder, i)) space = false;",
     "if (!XmaDecoder_HasInputSpace(self->decoder, i)) { space = false; break; }"),
    ("wrong submitted state", "buffer->state = 3;", "buffer->state = 2;"),
    ("omit empty-stream initialization",
     "if (empty) XmaDecoder_SetReadPosition", "if (false) XmaDecoder_SetReadPosition"),
    ("reset the first stream like subsequent streams",
     "i != 0 && XmaDecoder_IsInputEmpty(self->decoder, i)",
     "XmaDecoder_IsInputEmpty(self->decoder, i)"),
    ("wrong stream packet bit stride", "(uint32_t(i) << 14) + 32", "(uint32_t(i) << 13) + 32"),
    ("saturate instead of truncate loop count",
     "static_cast<uint8_t>(buffer->loopCount)",
     "buffer->loopCount > 255 ? 255 : static_cast<uint8_t>(buffer->loopCount)"),
    ("wrong loop end", "loop.endBits = buffer->loops[i].endBits;",
     "loop.endBits = buffer->loops[i].startBits;"),
    ("wrong pending subframe shift", "self->pendingPosition[i].subframe >> 7",
     "self->pendingPosition[i].subframe >> 8"),
    ("leave the pending marker set", "self->pendingPosition[0].bits = 0;",
     "self->pendingPosition[0].bits = 1;"),
    ("invert final empty-input result",
     "if (!XmaDecoder_IsInputEmpty(self->decoder, i)\n            &&",
     "if (XmaDecoder_IsInputEmpty(self->decoder, i)\n            &&"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/audio/xma_source.cpp").read_text()
    spec = Path(__file__).with_name("xma_source_submit_buffers.py")
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
