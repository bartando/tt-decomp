"""Inclusive padded x/z bounds, all nine active flags, and hit side effects.
The PPC ignores r4 and f1: radius cannot affect the answer.
"""
import math
from liftcheck.spec import *

FUNCTION = "gmPracticeTarget_IsPointOnTarget"
ADDRESS = 0x82113C38
SOURCE = "src/game/drill/pong_drill.cpp"
TRIALS = 1500
EXTERNS = {"g_practiceTargetGrid": 0x82617C90}


def inputs(t):
    r = t.rng
    padding = r.choice([0.025, 0.0, 0.1, -0.025])
    t.wf32(0x825C8144, padding)
    t.wf32(0x8271A360, r.uniform(-5, 5))
    bounds = []
    for i in range(9):
        xlo = (i % 3) - 1.5
        zlo = (i // 3) - 1.5
        # Other two corner pairs are deliberately unrelated: only 0/1 and 6/7 matter.
        zone = [xlo, zlo, r.uniform(-10, 10), r.uniform(-10, 10),
                r.uniform(-10, 10), r.uniform(-10, 10), xlo + 1, zlo + 1]
        for k, value in enumerate(zone):
            t.wf32(0x82617C90 + i * 32 + k * 4, value)
        bounds.append(zone)
        t.w32(0x825EB280 + 4 * i, r.choice([-1, 0, 1, 1, 2, 0x101]))
    i = t.index % 9
    if t.index % 4 == 0:
        # Force hits in later zones as well as the early return at zone zero.
        for k in range(9):
            t.w32(0x825EB280 + 4 * k, int(k == i))
        x, z = bounds[i][0] + .5, bounds[i][1] + .5
    else:
        edge = r.choice([0.0, .000001, -.000001, padding, -padding, .5, 1.0])
        x = r.choice([bounds[i][0] - edge, bounds[i][6] + edge, float('nan'), float('inf')])
        z = r.choice([bounds[i][1] - edge, bounds[i][7] + edge, bounds[i][1] + .5, float('nan')])
    point = t.alloc(16, 'point')
    for k, v in enumerate([x, r.uniform(-10, 10), z, r.uniform(-10, 10)]):
        t.wf32(point + 4 * k, v)
    target = t.alloc(0x70, 'target')
    t.w8(target + 0x64, r.choice([0, 1, 0x80]))
    t.args(r3=target, r4=t.u32(), r5=point, f1=r.choice([-100.0, 0.0, 100.0, math.nan]))
