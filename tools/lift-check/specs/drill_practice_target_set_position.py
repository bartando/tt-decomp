"""0x82113BA8 loads from r4 (lvx128), not from incoming VMX argument registers.

All vector bits copy exactly, with lvx alignment; x/z clamping uses scalar
fsel semantics, and y receives the stored height offset. Covers aliases and
noncanonical clamp bytes; poison VMX registers make the ABI test explicit.
"""
from liftcheck.spec import *

FUNCTION = "gmPracticeTarget_SetPosition"
ADDRESS = 0x82113BA8
SOURCE = "src/game/drill/pong_drill.cpp"
TRIALS = 1600


def inputs(t):
    r = t.rng
    table = t.alloc(0x30, 'table')
    width = r.choice([1.5224, 0.0, -0.0, -2.0, 2.0, r.uniform(.1, 8)])
    length = r.choice([2.7439, 0.0, -0.0, -4.0, 4.0, r.uniform(.1, 8)])
    t.wf32(table + 0x10, width)
    t.wf32(table + 0x18, length)
    target = t.alloc(0x90, 'targetAndGuard') + 16
    clamp = r.choice([0, 0, 1, 2, 0x80, 0xFF])
    t.w8(target + 0x17, clamp)
    t.wf32(target + 0x28, r.choice([0.0, -0.0, .001, r.uniform(-2, 2)]))
    # No table access is allowed when clamping is disabled.
    t.w32(0x8271A304, table if clamp else 0)
    source = t.alloc(32, 'source') if t.index % 4 else target + 0x50
    for k, scale in enumerate([width * .5, 2., length * .5, 1.]):
        value = r.choice([0., -0., scale, -scale, scale + .001, -scale - .001,
                          r.uniform(-10, 10), float('nan'), float('inf'), -float('inf')])
        t.wf32(source + k * 4, value)
    if t.index % 5 == 0:
        t.w32(source + 12, r.choice([1, 0x80000000, 0x7FA12345, t.u32()]))
    t.args(r3=target, r4=source + r.randrange(16),
           v0=[81., 82., 83., 84.], v3=[91., 92., 93., 94.], v4=[71., 72., 73., 74.])
