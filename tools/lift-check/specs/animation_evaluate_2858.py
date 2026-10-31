"""0x820C2858: evaluate at duration*phase, advance, then reload the new phase.

Both callees are modeled: evaluation replaces entry data/phase; advancement
stores an independent result after that replacement. No incoming FP args.
"""
import struct
from liftcheck.spec import *

FUNCTION = 'LocomotionStateAnim_2858'
ADDRESS = 0x820C2858
SOURCE = 'src/anim/animation_timing.cpp'
TRIALS = 240
FP_CONTRACT = 'off'


def u(c, a): return int.from_bytes(c.read(a, 4), 'big')


def evaluate(c):
    frame = c.r(5)
    entry = u(c, frame)
    c.write(entry + 0x1C, c.read(frame + 4, 4))
    c.write(entry + 0x14, c.read(frame + 8, 4))
    c.write(frame + 0x20, b'EVAL')
    c.ret(r3=0x12345600, f1=-987.0)


def advance(c):
    entry = c.r(3)
    frame = u(c, entry + 0x30)
    c.write(entry + 0x14, c.read(frame + 12, 4))
    c.ret(f1=345.0)


CALLS = {
    0x822488E0: model(evaluate, args=('r3', 'r4', 'r5', 'r6', 'r7', 'f1')),
    0x820C28B0: model(advance, args=('r3',)),
}


def inputs(t):
    rng = t.rng
    entry = t.alloc(0x40, 'entry')
    frame = t.alloc(0x40, 'frame and callback script')
    clip = t.alloc(0x20, 'clip')
    replacement = t.alloc(0x20, 'replacement clip')
    bits = (0, 0x80000000, 1, 0x80000001, 0x3F800000, 0xBF800000,
            0x3EAAAAAB, 0x3F7FFFFF, 0x7F800000, 0xFF800000, 0x7FC12345)
    t.w32(entry + 0x1C, clip)
    t.w32(entry + 0x14, rng.choice(bits) if t.index % 3 else t.u32())
    t.wf32(clip + 12, rng.uniform(-15, 15))
    if t.index % 5 == 0:
        t.w32(clip + 12, rng.choice(bits))
    t.w32(entry + 0x30, frame)
    t.w32(frame, entry)
    t.w32(frame + 4, replacement)
    t.w32(frame + 8, rng.choice(bits))
    t.w32(frame + 12, rng.choice(bits))
    # Wrong incoming FP parameters must not influence the result.
    t.args(r3=entry, r4=frame, r5=rng.getrandbits(32), f1=123.25, f2=-43.5)
