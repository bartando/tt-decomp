"""SDK render dispatcher: both bounds, dirty bits, all six kernel families,
format/channel lookup, float32 rate rounding and post-callback input progress.
The real [6][4][5] table is replaced by distinct observable kernel callbacks;
no resampler implementation is needed to test the dispatch contract.
"""
import struct

from liftcheck.spec import *

FUNCTION = "XmaRenderStream_Process"
ADDRESS = 0x82470CC0
SOURCE = "src/rage/audio/xma_source.cpp"
TRIALS = 1200


def process(ctx):
    stream = ctx.r(3)
    # Kernels advance both cursors; their return value is deliberately unrelated.
    ctx.write(stream + 8, struct.pack(">I", ctx.rng.getrandbits(32)))
    ctx.write(stream + 28, struct.pack(">I", ctx.rng.getrandbits(32)))
    ctx.ret(r3=ctx.rng.getrandbits(32))


CALLS = {f"kernel_{i}": model(process, args=("r3",), deref={"r3": 88})
         for i in range(120)}
CALLS["cached_kernel"] = model(process, args=("r3",), deref={"r3": 88})


def inputs(t):
    stream = t.alloc(88, "stream")
    # Include equality, past-end and the unsigned/signed boundary at both bounds.
    for limit_offset, cursor_offset in ((4, 8), (24, 28)):
        limit, cursor = t.pick(((1, 0), (17, 16), (17, 17), (17, 18),
                                (0, 0), (0x80000000, 0x7fffffff),
                                (0xffffffff, 0x80000000), (t.u32(), 0)))
        t.w32(stream + limit_offset, limit)
        t.w32(stream + cursor_offset, cursor)
    t.w8(stream + 12, t.rng.randrange(3))
    t.w8(stream + 13, t.pick((0, 1, 2, 3, 4, 5, 6, 7, 255)))
    numerator, denominator = t.pick(((48000, 48000), (24000, 48000),
                                    (44100, 48000), (0, 48000),
                                    (0x80000001, 2), (0xffffffff, 0xfffffffe),
                                    (t.u32(), t.u32() or 1)))
    t.w32(stream + 16, numerator)
    t.w32(stream + 32, denominator)
    t.w32(stream + 76, t.fake_fn("cached_kernel"))
    t.w32(stream + 80, t.pick((0, 1, 2, 3, 4, 0x80000000, 0xffffffff)))
    t.w32(stream + 84, (t.u32() & ~0x81) | t.pick((0, 1, 0x80, 0x81)))
    for i in range(120):
        t.w32(0x82006AF8 + 4 * i, t.fake_fn(f"kernel_{i}"))
    t.args(r3=stream)
