"""Mutation proof for the two renamed hot lifts. Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_render_dispatch_ctrlfp_mutations.py

Patches touch build-cache copies only. A behavioral FAIL (exit 1) is required;
BUILD, SPEC and UNSUPPORTED do not count as catching a mutation.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = {
    "xma_render_stream_process": ("src/rage/audio/xma_source.cpp", [
        ("process exhausted input", "initialOffset >= stream->inputFrames", "initialOffset > stream->inputFrames"),
        ("process full output", "stream->outputOffset >= stream->outputFrames", "stream->outputOffset > stream->outputFrames"),
        ("signed input bounds", "initialOffset >= stream->inputFrames", "int32_t(initialOffset) >= int32_t(stream->inputFrames)"),
        ("wrong dirty mask", "(stream->dirty & 3) != 0", "(stream->dirty & 1) != 0"),
        ("reselect on unrelated dirty bits", "(stream->dirty & 3) != 0", "stream->dirty != 0"),
        ("divide in double before rounding",
         "static_cast<float>(stream->inputRate)\n                                 / static_cast<float>(stream->outputRate)",
         "static_cast<float>(double(stream->inputRate) / double(stream->outputRate))"),
        ("wrong kernel family flag", "stream->flags & 0x80", "stream->flags & 0x40"),
        ("ignore rate specialization flag", "if (stream->flags & 1)", "if (true)"),
        ("lose uint32 rate wrap", "stream->inputRate * 2u == stream->outputRate", "uint64_t(stream->inputRate) * 2u == stream->outputRate"),
        ("old wrong table stride", "stream->format) * 5 + channelSlot", "stream->format) * 3 + channelSlot"),
        ("wrong channel slot", "(stream->channels >> 1) + 1", "(stream->channels >> 1)"),
        ("omit cached kernel update", "stream->process = g_xaudioRenderKernels[index];", "(void)index;"),
        ("omit dirty clear", "stream->dirty = 0;", "/* dirty not cleared */"),
        ("omit kernel call", "stream->process(stream);", "/* no processing */"),
        ("wrong progress return", "return stream->inputOffset - initialOffset;", "return stream->inputOffset;"),
    ]),
    "crt_ctrlfp": ("src/crt/ctrlfp.cpp", [
        ("return requested value", "return old ^ 0xF8u;", "return desired ^ 0xF8u;"),
        ("omit return inversion", "return old ^ 0xF8u;", "return old;"),
        ("omit exception-enable inversion", "((desired ^ 0xF8u) & mask) | (old & ~mask)", "(desired & mask) | (old & ~mask)"),
        ("preserve masked bits", "uint32_t updated = ((desired ^ 0xF8u) & mask) | (old & ~mask);",
         "uint32_t updated = ((desired ^ 0xF8u) & mask) | (old & mask);"),
        ("discard unmasked old bits", "uint32_t updated = ((desired ^ 0xF8u) & mask) | (old & ~mask);",
         "uint32_t updated = (desired ^ 0xF8u) & mask;"),
        ("ignore mask", "uint32_t updated = ((desired ^ 0xF8u) & mask) | (old & ~mask);",
         "uint32_t updated = desired ^ 0xF8u;"),
        ("truncate saved FPSCR", "uint32_t old = static_cast<uint32_t>(bits);",
         "uint32_t old = static_cast<uint32_t>(bits) & 0xffff;"),
        ("omit FPSCR write", '__asm__ volatile("mtfsf 255, %0" : : "f"(registerValue) : "memory");',
         "(void)registerValue;"),
    ]),
}


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec_name, (path, mutations) in CASES.items():
        source = (root / path).read_text()
        for label, old, new in mutations:
            assert source.count(old) == 1, f"mutation anchor changed: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        total += len(mutations)
        print(f"{spec_name}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
