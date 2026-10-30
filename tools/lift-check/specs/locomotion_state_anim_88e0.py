"""88E0: merge clip channels into a frame and optionally reset unmatched DOFs.

Covers empty/exhausted/disjoint/overlapping/duplicate sorted lists, key byte
and halfword boundaries, both mode/flag low bytes with noisy upper bits,
zero/one/multiple samples, fractional/negative/tie/huge/nonfinite sample times,
and zero/negative duration. Slot 4 evaluation and slot 13 resets are modeled;
receivers, order, sample positions, return boolean and all writes compare.
The unused r4 varies independently. No ignored memory or float tolerance.
Synthetic readable tables and virtual channels; actual channel evaluation,
invalid pointers, concurrent mutation and match replay are outside the spec.
"""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_88E0_g"
ADDRESS = 0x822488E0
SOURCE = "src/anim/locomotion.cpp"
TRIALS = 1000
RET = "r3"  # The original returns whether every frame channel matched.


def _evaluate(ctx):
    ctx.write(ctx.r(3) + 16, struct.pack(">f", ctx.f(1)))
    ctx.write(ctx.r(3) + 20, b"eval")


def _reset(ctx):
    ctx.write(ctx.r(3) + 16, b"reset!!!")


CALLS = {
    "channel.vfn_4": model(_evaluate, args=("r3", "f1")),
    "channel.vfn_13": model(_reset, args=("r3",)),
}


def inputs(t):
    rng = t.rng
    edge_keys = [0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x10000, 0x10001,
                 0x7FFFFF, 0x800000, 0xFF0000, 0xFFFFFF]
    pool = edge_keys + [rng.randrange(1 << 24) for _ in range(12)]
    case = rng.randrange(8)
    clip_keys = sorted(rng.choices(pool, k=rng.choice([0, 1, 2, 3, 8, 17])))
    frame_keys = sorted(rng.choices(pool, k=rng.choice([0, 1, 2, 5, 13])))
    if case == 0:
        frame_keys = clip_keys[:]
    elif case == 1:
        clip_keys = []
    elif case == 2:
        frame_keys = []
    elif case == 3:
        clip_keys, frame_keys = [0, 2, 4, 6], [1, 2, 3, 6, 7]
    elif case == 4:
        clip_keys, frame_keys = [0xFFFFFF], [0, 1, 0xFFFFFF]
    elif case == 5:
        clip_keys, frame_keys = [0, 1], [0, 1, 2, 3]
    elif case == 6:
        clip_keys, frame_keys = [1, 1, 1, 2], [1, 1, 2, 2]

    clip = t.alloc(48, "clip")
    frame = t.alloc(32, "frame")
    clip_table = t.alloc(max(4, len(clip_keys) * 4), "clipChannels")
    for i, key in enumerate(clip_keys):
        channel = t.alloc(16, f"clipChannel{i}")
        t.w8(channel, key >> 16)
        t.w16(channel + 2, key)
        t.w32(clip_table + i * 4, channel)
    frame_table = t.alloc(max(4, len(frame_keys) * 4), "frameChannels")
    vtable = t.vtable("channel", 14)
    for i, key in enumerate(frame_keys):
        channel = t.alloc(32, f"frameChannel{i}")
        t.w32(channel, vtable)
        t.w8(channel + 5, key >> 16)
        t.w16(channel + 6, key)
        t.w32(frame_table + i * 4, channel)
    samples = rng.choice([0, 1, 2, 3, 17, 0x7FFF, 0x8000, 0xFFFF])
    duration = rng.choice([0.0, -0.0, 0.125, 1.0, 2.0, 7.25, -1.0, float("inf")])
    time = rng.choice([0.0, -0.0, 0.25, 0.5, 0.75, 1.0, -0.5, 3.25,
                       1e30, -1e30, float("inf"), -float("inf"), float("nan"),
                       rng.uniform(-5, 5)])
    t.w16(clip + 10, samples)
    t.wf32(clip + 12, duration)
    t.w32(clip + 36, clip_table if clip_keys else 0)
    t.w16(clip + 40, len(clip_keys))
    t.w32(frame + 8, frame_table if frame_keys else 0)
    t.w16(frame + 12, len(frame_keys))
    mode = rng.choice([0, 1, 2, 0x80, 0xFF])
    flags = rng.choice([0, 1, 2, 0x80, 0xFF])
    t.args(r3=clip, r4=rng.getrandbits(32), r5=frame,
           r6=(rng.getrandbits(24) << 8) | mode,
           r7=(rng.getrandbits(24) << 8) | flags, f1=time)
