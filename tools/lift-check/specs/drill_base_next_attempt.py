"""Attempt bookkeeping, mode publication, target refresh and ordered UI messages."""
from liftcheck.spec import *

FUNCTION = "pongTrainingDrill::NextAttempt"
ADDRESS = 0x8210D128
SOURCE = "src/game/drill/pong_drill.cpp"
TRIALS = 1200


def _notify(ctx):
    # The missed-attempt call only supplies three arguments; later messages set r6.
    if ctx.r(3) == 0x5009:
        ctx.rec.gpr[3] = 0


CALLS = {
    "drill.vfn_17": stub(ret=lambda c: c.rng.choice([0, 1, 5, 7]), args=("r3",), deref={"r3": 0x24}),
    "drill.vfn_19": stub(ret=lambda c: c.rng.randrange(256), args=("r3",), deref={"r3": 0x24}),
    "drill.vfn_25": stub(ret="void", args=("r3",), deref={"r3": 0x24}),
    "drill.vfn_32": stub(ret=lambda c: c.rng.choice([0, 1, 2, 0x80]), args=("r3",), deref={"r3": 0x24}),
    "NotifyUIEvent": model(_notify, args=("r3", "r4", "r5", "r6")),
}


def inputs(t):
    r = t.rng
    t.w32(0x826063A4, t.alloc(0x224, "robot"))
    t.w32(0x82606614, t.alloc(0xC0, "hud"))
    config = t.alloc(0x80, "config")
    t.w32(config + 0x10, r.randrange(0, 20))
    drill = t.alloc(0x40, "drill")
    t.w32(drill, t.vtable("drill", slots=33))
    t.w32(drill + 0x20, config)
    t.w32(drill + 4, r.choice([-2, -1, 0, 1, 3, 8]))
    successes = r.randrange(0, 12)
    t.w32(drill + 8, successes)
    t.w32(drill + 12, r.choice([successes, successes - 1]))
    t.w8(drill + 0x18, r.choice([0, 0, 1, 0x80]))
    t.args(r3=drill, r4=r.choice([-2, -1, 0, 1, 1, 2, 5]))
