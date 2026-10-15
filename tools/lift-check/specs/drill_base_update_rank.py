"""pongTrainingDrill::UpdateRank (slot 27, 0x8210D488): rank from the successes beyond
MinNumSuccesses, and the saved best rank per drill."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongTrainingDrill::UpdateRank"
ADDRESS = 0x8210D488
SOURCE = "src/game/drill/pong_drill.cpp"
EXTERNS = {"floorf": 0x82431910, "floor": 0x82431910}

CALLS = {
    0x82431910: run(),                                                # floor
    "RoundHalfAwayFromZero": run(),                                   # 0x8210CB88
    "drill.vfn_17": stub(ret=lambda ctx: ctx.rng.randrange(0, 12)),  # GetDrillTypeIndex
}


def inputs(t):
    rng = t.rng
    config = t.alloc(0x80, "config")
    minimum = rng.randrange(0, 8)
    total = minimum + rng.choice([0, 0, 1, 2, 5])
    t.w32(config + 0x10, total)
    t.w32(config + 0x14, minimum)
    drill = t.alloc(0x40, "drill")
    t.w32(drill, t.vtable("drill", slots=33))
    t.w32(drill + 0x20, config)
    t.w32(drill + 0x08, rng.randrange(max(0, minimum - 2), total + 1))
    t.w32(drill + 0x10, rng.randrange(0, 6))
    progress = t.alloc(0x10, "trainingProgress")
    t.w32(progress + 4, rng.randrange(0, 4))
    t.w32(0x8271A31C, progress)
    saves = t.alloc(4 * 64, "saveData", fill=bytes(rng.choice([0, 1, 3, 5]) if i % 4 == 3 else 0
                                                    for i in range(4 * 64)))
    t.w32(0x8271A35C, saves)
    t.args(r3=drill, r4=rng.choice([0, 1]))
