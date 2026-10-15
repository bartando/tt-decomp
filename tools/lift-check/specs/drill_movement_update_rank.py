"""pongDrillMovement::UpdateRank (slot 27, 0x8210E208): rank 0..5 from the time left,
and the saved best rank per drill. floor and the rounding helper run the game's code."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::UpdateRank"
ADDRESS = 0x8210E208
SOURCE = "src/game/drill/pong_drill.cpp"

EXTERNS = {"floorf": 0x82431910, "floor": 0x82431910}

CALLS = {
    0x82431910: run(),                                   # floor
    "RoundHalfAwayFromZero": run(),                      # 0x8210CB88
    "drill.vfn_17": stub(ret=lambda ctx: ctx.rng.randrange(0, 12)),  # GetDrillTypeIndex
}


def inputs(t):
    rng = t.rng
    data = t.alloc(0x80, "movementData")
    total = rng.randrange(0, 10)
    t.w32(data + 0x10, total)                                    # TotalNumTries
    drill_time = rng.uniform(5.0, 90.0)
    t.wf32(data + 0x6C, drill_time)                              # DrillTime
    t.wf32(data + 0x70, rng.choice([rng.uniform(0.0, drill_time), drill_time, 0.0]))  # HighestRankTime

    drill = t.alloc(0x40, "drill")
    t.w32(drill, t.vtable("drill", slots=33))
    t.w32(drill + 0x38, data)
    t.w32(drill + 0x08, total + rng.randrange(-2, 2))            # successes
    t.w32(drill + 0x10, rng.randrange(0, 6))                     # rank so far
    t.wf32(drill + 0x28, rng.choice([rng.uniform(-1.0, drill_time), 0.0, -0.0,
                                     rng.uniform(0.0, 3.0)]))   # time left

    progress = t.alloc(0x10, "trainingProgress")
    t.w32(progress + 4, rng.randrange(0, 4))
    t.w32(0x8271A31C, progress)
    saves = t.alloc(4 * 64, "saveData", fill=bytes(rng.choice([0, 1, 3, 5, 0xFF]) if i % 4 == 3
                                                    else (0xFF if rng.random() < 0.1 else 0)
                                                    for i in range(4 * 64)))
    t.w32(0x8271A35C, saves)
    t.args(r3=drill, r4=rng.choice([0, 1]))
