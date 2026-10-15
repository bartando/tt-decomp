"""pongTrainingDrill::ApplyTargetSet (slot 25, 0x8210D380): shows TableTargetSetID on the
practice target for drills that use targets."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongTrainingDrill::ApplyTargetSet"
ADDRESS = 0x8210D380
SOURCE = "src/game/drill/pong_drill.cpp"

CALLS = {
    "drill.vfn_12": stub(ret=lambda ctx: ctx.rng.choice([0, 1])),     # IsScoreValid
    "drill.vfn_17": stub(ret=lambda ctx: ctx.rng.choice([0, 0, 3, 7])),  # GetDrillTypeIndex
}


def inputs(t):
    rng = t.rng
    t.w32(0x826063A8, t.alloc(0x80, "practiceTarget"))
    config = t.alloc(0x80, "config")
    drill = t.alloc(0x40, "drill")
    t.w32(drill, t.vtable("drill", slots=33))
    t.w32(drill + 0x20, config)
    t.args(r3=drill)
