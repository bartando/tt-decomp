"""Hit trail selection, low-byte input gate, both optional trails, setup/reset order."""
from liftcheck.spec import *

FUNCTION = "game_2010"
ADDRESS = 0x82282010
SOURCE = "src/game/ball/pong_ball.cpp"
TRIALS = 600

CALLS = {
    "io_Input_poll_9D68": stub(ret=lambda c: c.rng.choice([0, 1, 0x100, 0x10000, 0x101, 0xFFFFFFFF])),
    "trail.vfn_3": stub(ret="void", args=("r3", "r4", "r5", "r6"), deref={"r6": 32}),
    "trail.vfn_2": stub(ret="void"),
}


def inputs(t):
    node = t.alloc(0x150, "ball", ctype="gmBallNode")
    for off in (0xAC, 0xB0):
        trail = t.alloc(16, "trail")
        t.w32(trail, t.vtable("trail", 4))
        t.w32(node + off, t.rng.choice([0, trail, trail]))
    t.w32(0x825C9A2C, t.rng.choice([0, 0, -1, 1, 2]))
    t.w8(0x825C5EC8 + 0x48, t.rng.choice([0, 0, 1, 0x80, 0xFF]))
    t.w8(0x825C5EC8 + 0x30, t.rng.choice([0, 1]))
    t.args(r3=node, r4=t.rng.choice([0, 1, 2, 3, -1, 0x12345678]))
