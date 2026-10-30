"""Shader-instance unbind: inline device dispatch, MSB-first dirty runs and clears.

The image has 87 {u32 offset, u32 default} render entries at 0x825B1F90
and 20 {u16 unused, u16 offset, u32 default} sampler entries at 0x825B2248.
Native trials keep padding bits clear: randomizing them dispatches through
unrelated data beyond the tables. Device method pointers live inline at
+96+offset and +484+offset; the device's first word is not a vtable.

Patched-table trials vary offsets/defaults, poison the sampler entry's upper
halfword, and extend samplers to all 32 states to exercise bit 63 and full runs.
Callbacks compare all arguments, check that clears happen last, and sometimes
enable/disable the sampler pass to test the flags reload. No memory is ignored.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "grmShaderInstance_Unbind"
ADDRESS = 0x82159CF0
SOURCE = "src/rage/rage_grm.cpp"


def device_call(ctx):
    device = ctx.r(3)
    instance, next_flags = struct.unpack(">II", ctx.read(device + 0x280, 8))
    assert all(struct.unpack(">II", ctx.read(instance + 516, 8))), "cleared before dispatch finished"
    ctx.write(instance + 692, struct.pack(">I", next_flags))


CALLS = {
    **{f"render_{offset}": model(device_call, args=("r3", "r4"))
       for offset in range(0, 388, 4)},
    **{f"sampler_{offset}": model(device_call, args=("r3", "r4", "r5"))
       for offset in range(0, 128, 4)},
}


def dirty_word(t, valid_bits):
    valid = sum(1 << (63 - bit) for bit in valid_bits)
    # Empty, dense, alternating, singleton and separated runs, in both halves.
    mask = t.rng.choice([0, (1 << 64) - 1, 0xAAAAAAAAAAAAAAAA,
                         0x5555555555555555, 0xF00000FF8000000F,
                         1 << t.rng.randrange(64), t.rng.getrandbits(64)])
    return mask & valid


def inputs(t):
    rng = t.rng
    instance = t.alloc(704, "shader_instance")
    device = t.alloc(0x290, "device")
    # Install actual inline slots; retain unrelated random device bytes.
    for offset in range(0, 388, 4):
        t.w32(device + 96 + offset, t.fake_fn(f"render_{offset}"))
    for offset in range(0, 128, 4):
        t.w32(device + 484 + offset, t.fake_fn(f"sampler_{offset}"))
    t.w32(instance + 700, device)
    flags = rng.choice([0, 1, 2, 3, t.u32()])
    next_flags = (flags & ~3) | rng.randrange(4)
    t.w32(instance + 692, flags)
    t.w32(device + 0x280, instance)
    t.w32(device + 0x284, next_flags)
    t.w32(instance + 516, t.u32() | 1)
    t.w32(instance + 520, t.u32() | 1)

    patched = rng.randrange(3) == 0
    if patched:
        for index in range(87):
            t.w32(0x825B1F90 + index * 8, rng.randrange(97) * 4)
            t.w32(0x825B1F94 + index * 8, t.u32())
        for index in range(32):
            entry = 0x825B2248 + index * 8
            t.w16(entry, rng.randrange(1, 65536))
            t.w16(entry + 2, rng.randrange(32) * 4)
            t.w32(entry + 4, t.u32())

    t.w64(instance + 320, dirty_word(t, range(64)))
    t.w64(instance + 328, dirty_word(t, range(23)))
    states = 32 if patched else 20
    valid_sampler_bits = [half * 32 + state for half in range(2) for state in range(states)]
    for word in range(16):
        t.w64(instance + 384 + word * 8, dirty_word(t, valid_sampler_bits))
    t.args(r3=instance)
