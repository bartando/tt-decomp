"""Nine ordered quads from independently scaled x/z boundary arrays."""
from liftcheck.spec import *

FUNCTION = 'gmPracticeTarget_LayOutTableGrid'
ADDRESS = 0x821132B0
SOURCE = 'src/game/match/pong_match.cpp'
TRIALS = 1200
EXTERNS = {'g_practiceTargetGrid': 0x82617C90}


def inputs(t):
    table = t.alloc(0x30, 'table')
    t.w32(0x8271A304, table)
    for off in (0x10, 0x18):
        t.wf32(table + off, t.rng.choice([0., -0., t.rng.uniform(-10, 10), 1.5224, 2.7439]))
    for i in range(8):
        t.wf32(0x825C99E0 + 4 * i, t.rng.uniform(-2, 2))
    for i in range(72):
        t.w32(0x82617C90 + 4 * i, t.u32())
    t.args(r3=t.u32())
