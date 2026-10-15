"""pongBallInstance's message handler (msgMsgSink base at +0x50, slot 1, 0x822803F0):
include-flag changes, level removal/activation, flag55 and time stamps."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongBallInstance_HandleMessage"
ADDRESS = 0x822803F0
SOURCE = "src/game/ball/pong_ball.cpp"

IDS = [1, 2, 7, 0xF, 0x10, 0x11, 0x12, 0x13, 0x14, 0x2A, 0x2B, 0x381F, 0x3849, 0x838, 0x83B, 0x83C,
       0x849, 0x84B, 0x86B, 0x2801, 0x2802, 0x2803, 0x23, 0, 0xFFFF]

CALLS = {
    0x8227FDB0: stub(ret="void"),           # UpdatePhysicsState
    0x822C4B60: stub(ret="void"),           # game_4B60: out of the level
    0x822C4980: stub(),                     # back into the level
    0x822801B8: stub(ret="void", args=("r3", "r4")),   # ActivateBall
}


def inputs(t):
    rng = t.rng
    inst = t.alloc(0xD0, "inst")
    arch = t.alloc(0x20, "arch")
    t.w32(inst + 4, arch)
    t.w16(inst + 8, rng.randrange(16))
    t.w8(inst + 0x55, rng.choice([0, 1]))

    level = t.alloc(0x20, "level")
    states = t.alloc(16, "states", fill=bytes(rng.choice([0, 1, 8, 3]) for _ in range(16)))
    t.w32(level + 0x1C, states)
    t.w32(0x826065E4, level)
    t.w32(0x825F5BD0, t.alloc(0x10, "sim"))

    loop = t.alloc(0x250, "loop")
    t.w8(loop + 0x242, rng.choice([0, 1]))
    t.w32(0x825EAB30, loop)
    t.w32(0x825CAEB8 + 0x28, t.u32())       # sysTimeManager stamp

    msg = t.alloc(0x10, "msg")
    t.w16(msg, rng.choice(IDS))
    t.args(r3=inst + 0x50, r4=msg)
