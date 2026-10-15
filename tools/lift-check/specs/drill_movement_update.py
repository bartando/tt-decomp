"""pongDrillMovement::Update (slot 6, 0x8210DC78): the clock with its countdown beeps,
the end of the drill, and scoring a player who stands on the target."""
import zlib

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::Update"
ADDRESS = 0x8210DC78
SOURCE = "src/game/drill/pong_drill.cpp"



def _post_fmt(ctx):
    # The format string is "i", too short for lift-check to compare as text, and
    # the variadic argument (r6) isn't compared at all: record a checksum of both
    # in place of the pointer (r5).
    fmt = ctx.read(ctx.r(5), 2)
    ctx.rec.gpr[5 - 3] = zlib.crc32(bytes(fmt) + ctx.r(6).to_bytes(4, "big"))


CALLS = {
    # r4 is never set by the caller and neither it nor f1 is read by the callee;
    # compare the rest.
    "gmPracticeTarget_IsPointOnTarget": stub(ret=lambda ctx: ctx.rng.choice([0, 1]),
                                             args=("r3", "r5", "f1")),
    "PostPageGroupMessageFmt": model(_post_fmt),
    "drill.vfn_9": stub(ret="void", args=("r3", "r4")),         # NextAttempt(1)
}


def inputs(t):
    rng = t.rng
    t.w32(0x826063A8, t.alloc(0x80, "practiceTarget"))
    match = t.alloc(0x50, "match")
    t.w32(match + 0x44, t.alloc(0x40, "playerTransform"))
    t.w32(0x825EAB28, match)

    data = t.alloc(0x80, "movementData")
    t.wf32(data + 0x64, rng.uniform(0.05, 0.5))                       # DetectRadius
    t.wf32(data + 0x78, rng.choice([rng.uniform(0.1, 2.0), 0.0, -1.0]))  # TargetHitTime

    dt = rng.choice([rng.uniform(0.0, 0.1), 0.0, rng.uniform(0.5, 1.5)])
    drill = t.alloc(0x40, "drill")
    t.w32(drill, t.vtable("drill", slots=33))
    t.w32(drill + 0x38, data)
    t.w32(drill + 0x08, rng.randrange(0, 10))                         # successes
    t.wf32(drill + 0x14, rng.choice([-1.0, rng.uniform(0.0, 1.0), rng.uniform(-0.5, 0.5)]))
    t.w8(drill + 0x24, 1 if rng.random() < 0.15 else 0)               # finished
    mark = rng.choice([5.0, 4.0, 3.0, 2.0, 1.0, 0.0])
    t.wf32(drill + 0x28, rng.choice([mark + rng.uniform(-0.05, 0.1), mark, mark + dt,
                                     rng.uniform(-1.0, 60.0)]))      # time left
    t.wf32(drill + 0x2C, rng.choice([0.0, -0.5, rng.uniform(0.0, 1.0), dt]))  # hit hold timer
    t.args(r3=drill, f1=dt)
