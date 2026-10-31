"""Three court profiles, low-byte selectors, FMA and live overlapping fields."""
from liftcheck.spec import *
FUNCTION = "pongPlayer_GetCourtBounds"
ADDRESS = 0x821EFD20
SOURCE = "src/game/player/player_court.cpp"
TRIALS = 1000

def inputs(t):
    table = t.alloc(0x60, "court table")
    outputs = t.alloc(0x30, "outputs")
    for i in range(4, 17):
        t.wf32(table + i * 4, t.rng.uniform(-100, 100))
    if t.index < 200:
        for i in range(4, 17):
            t.wf32(table + i * 4, t.rng.choice([-1., -0., 0., 1., 100., float("inf"), float("nan")]))
    t.wf32(0x825c8080, t.rng.choice([0., .25, -1., float("nan")]))
    lo, hi = [(outputs, outputs + 16), (outputs, outputs), (table + 16, outputs),
              (outputs, table + 16), (table + 24, table + 32), (outputs + 4, outputs)][t.index % 6]
    selectors = [0, 1, 2, 255, 256, 0x12340001]
    t.args(r3=table, r4=t.rng.choice(selectors), r5=lo, r6=hi,
           r7=t.rng.choice(selectors), r8=t.rng.choice(selectors))
