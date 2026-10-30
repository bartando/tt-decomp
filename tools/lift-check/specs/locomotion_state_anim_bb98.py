"""BB98: slot-7 operation thunk, forwarding the complete channel operation.

Distinct source/destination, noisy integer flags and float bit patterns make
lost/swapped arguments observable. The virtual operation records arguments
and writes the source/weight/flags into the destination; all writes compare.
Only the callee is modeled. No ignored memory or tolerance; synthetic readable
objects, no actual channel interpolation or game replay.
"""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_BB98"
ADDRESS = 0x8224BB98
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000


def _operation(ctx):
    ctx.write(ctx.r(3) + 16, ctx.read(ctx.r(4), 16))
    ctx.write(ctx.r(3) + 32, struct.pack(">fII", ctx.f(1), ctx.r(5), ctx.r(6)))


CALLS = {f"channel.vfn_{i}": model(_operation, args=("r3", "r4", "f1", "r5", "r6"))
         for i in range(8)}


def inputs(t):
    rng = t.rng
    dst = t.alloc(64, "destination")
    src = t.alloc(64, "source")
    t.w32(dst, t.vtable("channel", 8))
    t.args(r3=dst, r4=src, r5=rng.getrandbits(32), r6=rng.getrandbits(32),
           f1=rng.choice([0.0, -0.0, -1.0, 1.0, float("inf"), -float("inf"),
                          float("nan"), 2 ** -149, rng.uniform(-20, 20)]))
