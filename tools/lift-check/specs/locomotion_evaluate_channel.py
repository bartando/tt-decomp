"""Evaluate the requested DOF from a matching channel, or reset it on a miss.

The original binary search executes on both sides. Observe the destination,
source pointer/content, scaled f1, callback order/effects and boolean result.
Cover empty/duplicate/mixed-type tables, uint16 sample counts, negative/zero/
finite/NaN/Inf times and durations. Destination key differs from the animation's
header. r4 is an unused ABI slot; r3/r5/f1 are meaningful at the evaluate call.
Limits: valid synthetic objects; virtual evaluate/reset bodies are boundary
models, not verified DOF implementations. No tolerance or ignored memory.
"""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_EvaluateChannel"
ADDRESS = 0x82248828
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000


def evaluate(ctx):
    # Copy the channel identity/padding and record the actual sample position.
    ctx.write(ctx.r(3) + 8, ctx.read(ctx.r(5), 4))
    ctx.write(ctx.r(3) + 12, struct.pack(">f", ctx.f(1)))


def reset(ctx):
    ctx.write(ctx.r(3) + 8, bytes.fromhex("deadbeef cafebabe"))


CALLS = {
    0x8224A390: run(),
    "dof.vfn_4": model(evaluate, args=("r3", "r5", "f1"), deref={"r5": 4}),
    "dof.vfn_13": model(reset, args=("r3",)),
}


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x30, "animation")
    dof = t.alloc(0x20, "destinationDof", floats=[12])
    t.w32(dof, t.vtable("dof"))
    count = rng.choice((0, 1, 2, 3, 7, 8, 31, 32, 129))
    query = rng.choice((0, 0xFFFF, 0x10000, 0x7FFFFF, 0x800000,
                        0xFFFFFF, rng.randrange(1 << 24)))
    mode = rng.randrange(8)
    keys = sorted(rng.sample(range(1 << 24), count))
    if mode == 0:
        keys = [query] * count
    elif count and mode < 5:
        query = keys[rng.choice((0, count // 2, count - 1, rng.randrange(count)))]
    elif mode == 5:
        keys = [max(1, key) for key in keys]
        query = 0
    elif mode == 6:
        keys = [min(0xFFFFFE, key) for key in keys]
        query = 0xFFFFFF
    table = 0
    if count:
        entries = t.alloc(count * 4, "keys", fill=b"".join(
            struct.pack(">BBH", key >> 16, rng.randrange(256), key & 0xFFFF) for key in keys))
        table = t.alloc(count * 4, "keyPointers", fill=b"".join(
            struct.pack(">I", entries + i * 4) for i in range(count)))
    t.w32(obj + 0x24, table)
    t.w16(obj + 0x28, count)
    t.w16(obj + 10, rng.choice((0, 1, 2, 3, 255, 0x7FFF, 0x8000, 0xFFFF)))
    t.w8(dof + 5, query >> 16)
    t.w16(dof + 6, query & 0xFFFF)
    values = (0.0, -0.0, 1.0, -1.0, 0.3, 7.0, float("inf"), -float("inf"), float("nan"))
    t.wf32(obj + 12, rng.choice((*values, rng.uniform(-100, 100))))
    time = struct.unpack(">f", struct.pack(">f", rng.choice((*values, rng.uniform(-10, 10)))))[0]
    t.args(r3=obj, r4=t.u32(), r5=dof, f1=time)
