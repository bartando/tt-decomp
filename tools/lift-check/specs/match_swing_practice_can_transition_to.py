"""gmLogicSwingPractice::CanTransitionTo (slot 13, 0x82102B60)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmLogicSwingPractice::CanTransitionTo"
ADDRESS = 0x82102B60
SOURCE = "src/game/match/pong_match.cpp"

# Slot 15 answers a bool (0 or 1); the original hands its r3 straight back
# (tail call), the lift normalises it, so a random r3 would be a false alarm.
def _can_transition(ctx):
    ctx.ret(r3=(ctx.r(4) ^ (ctx.r(3) >> 4)) & 1)


CALLS = {f"state{i}.vfn_15": model(_can_transition) for i in range(8)}


def inputs(t):
    rng = t.rng
    logic = t.alloc(0xA0, "logic", ctype="gmLogicSwingPractice")
    states = t.alloc(4 * 8, "states")
    for i in range(8):
        if rng.random() < 0.8:
            s = t.alloc(0x20, f"state{i}")
            t.w32(s, t.vtable(f"state{i}"))
            t.w32(states + 4 * i, s)
        else:
            t.w32(states + 4 * i, 0)
    t.w32(logic + 0x04, 8)
    t.w32(logic + 0x08, states)
    t.w32(logic + 0x0C, rng.choice([-1, -1, rng.randrange(8)]))
    t.args(r3=logic, r4=rng.choice([-5, -1, 0, 1, 1, 2, 7, 8, 9, 0x7FFFFFFF, rng.randrange(-20, 20)]))
