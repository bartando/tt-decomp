"""pongDrillMovement::NextAttempt (slot 9, 0x8210DEC0): ends the drill after the last try,
otherwise places the next target around the player with the drills' MWC generator.

The play area (0x821C9CD0) is modelled: min/max corners with the player inside.
The generator can't always be compared: each step is `mulld` then a plain `add`,
and lift-check runs that add as 32-bit, so the original's carry (the upper half
of the sum) comes out wrong (README, Limits: code that mixes 64- and 32-bit ops).
Starting from seed 0 keeps every number the position is built from exact: step
1 gives seed = carry0, carry = 0, and step 2's seed is a low half. The state the
original leaves behind is still wrong then, so the SetPosition model clears it
on both sides. A quarter of the trials start from (0, 0) or (0, 1) instead,
where every step stays exact and the final state is compared too.

The new position reaches gmPracticeTarget_SetPosition through a const pointer into
the stack, so lift-check compares all four lanes of it.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::NextAttempt"
ADDRESS = 0x8210DEC0
SOURCE = "src/game/drill/pong_drill.cpp"


def _side_bounds(ctx):
    rng = ctx.rng
    x0, x1 = sorted(rng.uniform(-4.0, 4.0) for _ in range(2))
    z0, z1 = sorted(rng.uniform(1.0, 7.0) for _ in range(2))
    ctx.write(ctx.r(5), struct.pack(">fff", x0, 0.0, z0))
    ctx.write(ctx.r(6), struct.pack(">fff", x1, 0.0, z1))
    ctx.ret(r3=ctx.r(3))  # a leaf that keeps r3, and the original relies on it


_exact_generator = [False]


def _set_position(ctx):
    if not _exact_generator[0]:
        ctx.write(0x825CA2C8, bytes(8))   # see above
    # Another leaf the original trusts to keep r3 (the target) and r5 (1). r3 goes
    # through ret(); lift-check clobbers r5 after the policy with this call's RNG
    # (r0 first, r5 second), so hand it r5's own value for that draw.
    ctx.ret(r3=ctx.r(3))
    r5, draw, real = ctx.r(5), [0], ctx.rng.getrandbits

    def getrandbits(k):
        draw[0] += 1
        v = real(k)
        return r5 if draw[0] == 2 else v
    ctx.rng.getrandbits = getrandbits


CALLS = {
    "pongTrainingDrill::NextAttempt": stub(ret="void"),
    "DrillMatch_GetSideBounds": model(_side_bounds),
    "gmPracticeTarget_SetPosition": model(_set_position),
}


def inputs(t):
    rng = t.rng
    t.w32(0x826063A8, t.alloc(0x80, "practiceTarget"))
    match = t.alloc(0x50, "match")
    transform = t.alloc(0x40, "playerTransform")
    t.floats(transform + 0x30, 4, -4.0, 7.0)
    t.w32(match + 0x44, transform)
    t.w32(0x825EAB28, match)
    _exact_generator[0] = rng.random() < 0.25
    t.w32(0x825CA2C8, 0)                                      # generator seed (see above)
    t.w32(0x825CA2CC, rng.choice([0, 1]) if _exact_generator[0] else rng.getrandbits(31))

    data = t.alloc(0x80, "movementData")
    total = rng.randrange(0, 10)
    t.w32(data + 0x10, total)                                 # TotalNumTries
    t.wf32(data + 0x60, rng.uniform(0.05, 0.8))               # TargetRadius
    t.wf32(data + 0x68, rng.uniform(-0.5, 0.5))               # VerticalOffset

    drill = t.alloc(0x40, "drill")
    t.w32(drill, t.vtable("drill", slots=33))
    t.w32(drill + 0x38, data)
    t.w32(drill + 0x04, total + rng.randrange(-3, 2))         # tries (the base call is a stub)
    t.w32(drill + 0x30, rng.randrange(0, 6))                  # previous target side
    t.args(r3=drill, r4=rng.choice([1, 1, 2, 0]))
