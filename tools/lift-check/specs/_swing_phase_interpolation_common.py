"""Shared clock/marker boundary inputs for both scalar swing phase helpers."""
from liftcheck.spec import *

EXTERNS = {"g_pongMatchTiming": 0x8271A2E8, "g_sysTimeManager": 0x825CAEB8}


def inputs(t):
    swing = t.alloc(0x90, "swing", floats=[(0x0C, 5), 0x28])
    record = t.alloc(0x140, "record")
    clip = t.alloc(0x20, "clip", floats=[0x0C])
    clock = t.alloc(0x40, "clock", floats=[0x30])
    t.w32(record + 0x10, clip)
    times = [-1, -0.0, 0, 0.25, 0.5, 1, 2, float("nan"), float("inf"), -float("inf")]
    for offset in (0x0C, 0x10, 0x14, 0x1C, 0x28):
        t.wf32(swing + offset, t.rng.choice(times + [t.rng.uniform(-2, 3)]))
    t.wf32(clock + 0x30, t.rng.choice(times + [t.rng.uniform(-2, 3)]))
    t.wf32(clip + 0x0C, t.rng.choice([-1, 0, 1.0e-40, 0.01, 0.1, 1, 2, float("nan"), float("inf")]))
    t.w16(record + 0x130, t.rng.choice([-32768, -1, 0, 7, 15, 30, 32767]))
    t.w16(record + 0x132, t.rng.choice([-32768, -1, 0, 7, 15, 30, 32767]))
    t.w32(t.sym("g_pongMatchTiming"), clock)
    t.wf32(t.sym("g_sysTimeManager") + 8, t.rng.choice([0, 1 / 60, 1 / 30, -0.1, 2, float("nan")]))
    t.args(r3=swing, r4=record)
