"""Inactive-instance queue: unsigned capacity gate and exact low-three state bits."""
from liftcheck.spec import *
FUNCTION = "BallPhysics_QueueInactive"
ADDRESS = 0x822C1B98
SOURCE = "src/game/ball/ball_playback.cpp"
TRIALS = 800


def inputs(t):
    rng = t.rng
    sim = t.alloc(0x40, "simulator")
    level = t.alloc(0x20, "level")
    states = t.alloc(0x10000, "states")
    handles = t.alloc(240, "queued handles")
    t.w32(sim + 4, level)
    t.w32(sim + 0x38, rng.choice([0, 1, 118, 119, 120, 121, 0xFFFFFFFF]))
    t.w32(sim + 0x3C, handles)
    t.w32(level + 0x1C, states)
    handle = rng.choice([0, 1, 65535, rng.randrange(65536)])
    t.w8(states + handle, rng.choice([0, 1, 2, 3, 5, 7, 8, 9, 0x81, 0x85, 0xF9, 0xFD, 0xFF]))
    t.args(r3=sim, r4=handle)
