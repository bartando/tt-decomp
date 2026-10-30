"""0x8247FE38: XAudio effect buffer selection and slot-6 dispatch.

Covers enabled/disabled effects, all nonzero low-three-bit formats, high bits,
null/unknown/current pool buffers, null and aliasing pool entries, and callback results.
The original passes an uninitialized stack word twice for zero-format active
items; the lift uses nulls, and zero-format descriptors are excluded here.
"""
from liftcheck.spec import *

FUNCTION = "rage::xaudioEffectBuffer_Process"
ADDRESS = 0x8247FE38
SOURCE = "src/rage/audio/xaudio_effect_buffer.cpp"
TRIALS = 1000
POOL_GLOBAL = 0x825E788C
CALLS = {"effect.vfn_6": stub(args=("r3", "r4", "r5"))}


def inputs(t):
    r = t.rng
    effect = t.alloc(8, "effect")
    interface = t.alloc(4, "interface")
    pool = t.alloc(20, "pool")
    current = t.alloc(4, "current")
    allocated0 = t.alloc(16, "buffer0")
    allocated1 = t.alloc(16, "buffer1")
    buffer0 = r.choice([0, allocated0])
    buffer1 = r.choice([0, buffer0, allocated1])
    unknown = t.alloc(16, "unknown")
    t.w32(interface, t.vtable("effect", slots=7))
    t.w32(effect, interface)
    t.w8(effect + 5, r.randrange(256))
    t.w8(effect + 6, (r.randrange(32) << 3) | r.randrange(1, 8))
    t.w32(pool + 12, buffer0)
    t.w32(pool + 16, buffer1)
    t.w32(POOL_GLOBAL, pool)
    t.w32(current, r.choice([0, buffer0, buffer1, unknown]))
    t.args(r3=t.alloc(8, "owner"), r4=effect, r5=current)
