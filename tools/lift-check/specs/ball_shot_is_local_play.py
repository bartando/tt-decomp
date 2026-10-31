"""822823E0: poll's low byte gates a post-call read of the play-mode word."""
import struct
from liftcheck.spec import *

FUNCTION = "BallShot_IsLocalPlay"
ADDRESS = 0x822823E0
SOURCE = "src/game/ball/ball_shot_simulation.cpp"
TRIALS = 1000


def _poll(ctx):
    value, mode = struct.unpack(">II", ctx.read(ctx.r(3), 8))
    ctx.write(0x825C9A2C, struct.pack(">I", mode))
    ctx.ret(r3=value)


CALLS = {"io_Input_poll_9D68": model(_poll)}


def inputs(t):
    rng = t.rng
    script = t.alloc(8, "poll script")
    t.w32(script, rng.choice([0, 1, 0x100, 0x101, 0xffffff00, 0xffffffff]))
    t.w32(script + 4, rng.choice([0, 1, 0xffffffff, rng.getrandbits(32)]))
    t.w32(0x825EAB28, script)
    t.w32(0x825C9A2C, rng.getrandbits(32))
    t.args()
