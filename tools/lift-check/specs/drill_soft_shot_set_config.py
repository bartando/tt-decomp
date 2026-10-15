"""pongDrillSoftShot::SetConfig (slot 1, 0x8210EDA0): keeps the config, and at +0x38 when
the config's IsOfType (slot 20) says gdDrillSoftShotData (class id at 0x825C74FC).
It was lifted as a "ScalarDestructor" that asked the drill, not the config."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillSoftShot::SetConfig"
ADDRESS = 0x8210EDA0
SOURCE = "src/game/drill/pong_drill.cpp"

# bool returns are 0 or 1 (see drill_movement_set_config).
CALLS = {
    "config.vfn_20": stub(ret=lambda ctx: ctx.rng.choice([0, 1]), args=("r3", "r4")),
}


def inputs(t):
    config = t.alloc(0x80, "config")
    t.w32(config, t.vtable("config", slots=33))
    t.w32(0x825C74FC, t.u32())  # gdDrillSoftShotData class id (.data)
    drill = t.alloc(0x40, "drill")
    t.args(r3=drill, r4=config)
