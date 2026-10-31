"""Random x/z placement through the real pointer-based SetPosition callee.
Both PRNG words, resulting vec4, height offset, clamp flags and guards compare.
"""
from liftcheck.spec import *

FUNCTION = 'gmPracticeTarget_PlaceRandomly'
ADDRESS = 0x82113A98
SOURCE = 'src/game/match/pong_match.cpp'
TRIALS = 1400
CALLS = {'gmPracticeTarget_SetPosition': run(args=('r3', 'r4'), deref={'r4': 16})}


def inputs(t):
    r = t.rng
    table = t.alloc(0x30, 'table')
    t.wf32(table + 0x10, r.uniform(.3, 5))
    t.wf32(table + 0x14, r.uniform(-.2, 2))
    t.wf32(table + 0x18, r.uniform(.3, 7))
    t.w32(0x8271A304, table)
    target = t.alloc(0x90, 'targetAndGuards') + 16
    t.w8(target + 0x17, r.choice([0, 1, 0x80]))
    t.wf32(target + 0x28, r.uniform(-.1, .1))
    t.w32(0x825CA2C8, t.u32())
    t.w32(0x825CA2CC, t.u32())
    t.args(r3=target, r4=t.u32())
