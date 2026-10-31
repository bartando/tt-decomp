"""Replay pose orchestration: cached sample/time, four rows, old-pose callback,
instance/level replacement, aligned scratch matrix and transform notification."""
import struct
from liftcheck.spec import *

FUNCTION = "gmBallNode_UpdateReplay"
ADDRESS = 0x82282110
SOURCE = "src/game/ball/ball_replay_update.cpp"
TRIALS = 1000


def u32(c, p):
    return struct.unpack(">I", c.read(p, 4))[0]


def w32(c, p, v):
    c.write(p, struct.pack(">I", v & 0xffffffff))


def spin(c):
    node, matrix = c.r(3), c.r(6)
    assert matrix % 16 == 0, "visual spin requires four aligned rows"
    script = u32(c, node + 0x148)
    w32(c, node + 0x74, u32(c, script))
    # The visual helper can change all four rows. Its own math has a separate spec.
    words = struct.unpack(">16I", c.read(matrix, 64))
    c.write(matrix, struct.pack(">16I", *(v ^ 0x80000000 for v in words)))


def previous(c):
    instance = c.r(3)
    c.write(instance + 0x60, c.read(c.r(4), 64))
    node = u32(c, instance + 0xC0)
    script = u32(c, node + 0x148)
    w32(c, node + 0x74, u32(c, script + 4))
    w32(c, 0x826065E4, u32(c, script + 8))


CALLS = {
    "BallNode_IntegrateVisualSpin": model(spin, args=("r3", "r5", "r6", "f1"),
                                         deref={"r5": 16, "r6": 64}),
    "instance.vfn_3": model(previous, args=("r3", "r4"), deref={"r4": 64}),
    "level.vfn_11": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x150, "ball node", ctype="gmBallNode")
    instances = [t.alloc(0xD0, f"instance{i}") for i in range(3)]
    for i, instance in enumerate(instances):
        t.w32(instance, t.vtable("instance", 4))
        t.w16(instance + 8, rng.choice([0, 1, 32768, 65535, rng.randrange(65536)]))
        t.floats(instance + 0x10, 16, -10, 10)
        t.floats(instance + 0x60, 16, -10, 10)
        t.w32(instance + 0xC0, node)
    levels = [t.alloc(4, f"level{i}") for i in range(2)]
    for level in levels:
        t.w32(level, t.vtable("level", 12))
    script = t.alloc(12, "callback script")
    for off, value in enumerate([rng.choice(instances), rng.choice(instances), rng.choice(levels)]):
        t.w32(script + 4 * off, value)
    t.w32(node + 0x148, script)
    t.w32(node + 0x74, instances[0])
    t.w32(0x826065E4, levels[0])
    replay = t.alloc(0x68CF0, "replay state")
    t.floats(replay + 0xE900, 8, -10, 10)
    times = [-1., -0., 0., 0.125, 1., 8., float("nan"), float("inf")]
    t.wf32(replay + 0x68CE4, rng.choice(times))
    t.wf32(replay + 0x68CE8, rng.choice(times))
    t.w32(0x8271A2EC, replay)
    t.args(r3=node)
