"""drill_base_increase_num_successes without checksum models: the debug message (longer
than 64 bytes) and the one-letter format string compare as text, the variadic r6
through args=.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongTrainingDrill::IncreaseNumSuccesses"
ADDRESS = 0x8210D400
SOURCE = "src/game/drill/pong_drill.cpp"

CALLS = {
    "PostPageGroupMessageFmt": stub(ret="void", args=("r3", "r4", "r5", "r6")),
}


def inputs(t):
    rng = t.rng
    t.w32(0x82606614, t.alloc(0xC0, "hud"))
    config = t.alloc(0x80, "config")
    total = rng.randrange(0, 12)
    t.w32(config + 0x10, total)
    drill = t.alloc(0x40, "drill")
    t.w32(drill + 0x20, config)
    t.w32(drill + 0x08, total + rng.randrange(-4, 2))
    t.args(r3=drill, r4=rng.choice([1, 1, 2, 0, -1]))
