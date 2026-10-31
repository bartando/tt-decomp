"""pongDrillMovement::NextAttempt (slot 9, 0x8210DEC0): ends the drill after the last try,
otherwise places the next target around the player with the drills' MWC generator.

The play area (0x821C9CD0) is modelled: min/max corners with the player inside.
The target-position callee executes in full on both sides: the ABI is r4
pointing at an aligned stack vec4 (the listing mislabels lvx128 as vmaddfp128).
Full-width random PRNG state is compared without clearing or ignoring it.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::NextAttempt"
ADDRESS = 0x8210DEC0
SOURCE = "src/game/drill/pong_drill.cpp"
TRIALS = 1200


def _side_bounds(ctx):
    rng = ctx.rng
    x0, x1 = sorted(rng.uniform(-4.0, 4.0) for _ in range(2))
    z0, z1 = sorted(rng.uniform(1.0, 7.0) for _ in range(2))
    ctx.write(ctx.r(5), struct.pack(">fff", x0, 0.0, z0))
    ctx.write(ctx.r(6), struct.pack(">fff", x1, 0.0, z1))
    ctx.ret(r3=ctx.r(3))  # a leaf that keeps r3, and the original relies on it


CALLS = {
    "pongTrainingDrill::NextAttempt": stub(ret="void"),
    "pongMatchSettings_GetCourtBounds": model(_side_bounds),
    "gmPracticeTarget_SetPosition": run(args=("r3", "r4"), deref={"r4": 16}),
}


def inputs(t):
    rng = t.rng
    target = t.alloc(0x80, "practiceTarget")
    t.w32(0x826063A8, target)
    t.wf32(target + 0x28, rng.uniform(-.1, .1))
    match = t.alloc(0x50, "match")
    transform = t.alloc(0x40, "playerTransform")
    t.floats(transform + 0x30, 4, -4.0, 7.0)
    t.w32(match + 0x44, transform)
    t.w32(0x825EAB28, match)
    t.w32(0x825CA2C8, t.u32())
    t.w32(0x825CA2CC, t.u32())

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
