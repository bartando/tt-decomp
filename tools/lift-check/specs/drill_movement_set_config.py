"""pongDrillMovement::SetConfig (slot 1, 0x8210DAE0): keeps the config, and as movement
data when its IsOfType (slot 20) says it is a gdDrillMovementData."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::SetConfig"
ADDRESS = 0x8210DAE0
SOURCE = "src/game/drill/pong_drill.cpp"

# bool returns are 0 or 1 here: the original tests only the low byte (MSVC), clang the
# whole register, and upper bits in a bool return are outside both ABIs.
CALLS = {
    "config.vfn_20": stub(ret=lambda ctx: ctx.rng.choice([0, 1]), args=("r3", "r4")),
}


def inputs(t):
    config = t.alloc(0x80, "config")
    t.w32(config, t.vtable("config", slots=33))
    t.w32(0x825C6BC4, t.u32())  # gdDrillMovementData class id (.data)
    drill = t.alloc(0x40, "drill")
    t.args(r3=drill, r4=config)
