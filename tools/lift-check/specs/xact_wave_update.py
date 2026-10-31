"""Shared memory/streaming wave worker, 0x8244AAE8.

Exact memory/call comparison; no ignored bytes or float tolerance. Both atomic
requests include 0, 1 and noncanonical nonzero words. Models exercise callback
changes to flags, state, voice and instance pointers, plus cleanup ordering.
Single-threaded execution checks CAS semantics, not concurrent interference or
Xenon interrupt masking. Downstream notification/instance work is isolated.
"""
import struct

from liftcheck.spec import *

FUNCTION = "xactWave_Update"
ADDRESS = 0x8244AAE8
SOURCE = "src/rage/audio/xact_sound.cpp"
TRIALS = 1000
RET = None


def word(ctx, address):
    return struct.unpack(">I", ctx.read(address, 4))[0]


def put(ctx, address, value):
    ctx.write(address, struct.pack(">I", value & 0xffffffff))


def notify(ctx):
    wave = ctx.r(3)
    assert ctx.r(4) == 13, "wrong stop notification"
    assert word(ctx, wave + 0x20) == 5, "notification must observe stopped state"
    put(ctx, wave + 0x20, word(ctx, wave + 0x44))
    put(ctx, wave + 0x28, word(ctx, wave + 0x48))
    put(ctx, wave + 0x3c, word(ctx, wave + 0x4c))


def update_instance(ctx):
    instance = ctx.r(3)
    wave = word(ctx, instance + 4)
    put(ctx, wave + 0x24, word(ctx, instance + 8))
    put(ctx, wave + 0x20, word(ctx, instance + 12))
    ctx.write(wave + 0x18, ctx.read(instance + 16, 1))
    put(ctx, wave + 0x28, word(ctx, instance + 20))


def get_voice_state(ctx):
    voice = ctx.r(3)
    wave = word(ctx, voice + 4)
    put(ctx, ctx.r(4), word(ctx, voice + 12))
    ctx.write(wave + 0x18, ctx.read(voice + 16, 1))
    put(ctx, wave + 0x20, word(ctx, voice + 20))
    put(ctx, wave + 0x28, word(ctx, voice + 24))
    ctx.ret(r3=word(ctx, voice + 8))


def detach(ctx):
    instance, retained = ctx.r(3), ctx.r(4)
    wave = word(ctx, instance + 4)
    assert word(ctx, wave + 0x3c) == 0, "clear retained object before detaching"
    assert word(ctx, wave + 0x28) == instance, "keep instance until detach returns"
    assert word(ctx, wave + 0x20) == 5, "stop must overwrite callback state"
    # A callback can replace both pointers; the caller must still clear the
    # instance and destroy the originally saved retained object afterwards.
    put(ctx, wave + 0x28, word(ctx, instance + 20))
    put(ctx, wave + 0x3c, word(ctx, instance + 24))


def destroy_retained(ctx):
    wave = word(ctx, ctx.r(3) + 4)
    assert ctx.r(4) == ctx.r(5) == 0, "destroy arguments must both be zero"
    assert word(ctx, wave + 0x28) == 0, "clear instance before destroying retained object"
    put(ctx, ctx.r(3) + 8, 0xd3570eed)


CALLS = {
    "atSingleton_A6C8": model(notify),
    # Run the actual finalizer: sets flags bit 0x10, releases instance slot 7,
    # and clears the pointer. It is separate from the instance retirement call.
    "xactWave_Finalize": run(),
    "atSingleton_2378_g": stub(ret="void"),
    "instance.vfn_7": stub(ret="void", args=("r3",)),
    "instance.vfn_8": model(update_instance, args=("r3",)),
    "instance.vfn_31": model(detach, args=("r3", "r4")),
    "voice.vfn_0": model(get_voice_state, args=("r3", "r4")),
    "retained.vfn_2": model(destroy_retained, args=("r3", "r4", "r5")),
}

STATES = (0, 1, 2, 3, 4, 5, 6, 0x7fffffff, 0x80000000, 0xffffffff)
REQUESTS = (0, 1, 2, 0x100, 0x80000000, 0xffffffff)
_trial = 0


def inputs(t):
    global _trial
    case = _trial
    _trial += 1
    rng = t.rng
    wave = t.alloc(0x50, "wave", ctype="XactWaveRuntime")
    instances = [t.alloc(0x20, f"instance{i}") for i in range(2)]
    voices = [t.alloc(0x20, f"voice{i}") for i in range(2)]
    retained = [t.alloc(0x10, f"retained{i}") for i in range(2)]
    ivt, vvt, rvt = t.vtable("instance", 32), t.vtable("voice", 1), t.vtable("retained", 3)
    for instance in instances:
        t.w32(instance, ivt)
        t.w32(instance + 4, wave)
        t.w32(instance + 8, rng.choice((0, *voices)))
        t.w32(instance + 12, rng.choice((3, 4, *STATES)))
        t.w8(instance + 16, rng.choice((0, 0x80, rng.randrange(256))))
        t.w32(instance + 20, rng.choice((0, *instances)))
        t.w32(instance + 24, rng.choice((0, *retained)))
    for voice in voices:
        t.w32(voice, vvt)
        t.w32(voice + 4, wave)
        t.w32(voice + 8, rng.choice((0, 1, 0x7fffffff, 0x80000000, 0xffffffff)))
        t.w32(voice + 12, rng.choice((0, 1, 2, 0x100, 0x80000000, 0xffffffff)))
        t.w8(voice + 16, rng.choice((0, 0x80, rng.randrange(256))))
        t.w32(voice + 20, rng.choice((3, 4, *STATES)))
        t.w32(voice + 24, rng.choice((0, *instances)))
    for obj in retained:
        t.w32(obj, rvt)
        t.w32(obj + 4, wave)

    # Blocked cases must leave both request words untouched. Most trials are
    # unblocked so their less common completion/cleanup paths get exercised.
    flags = rng.randrange(256) & ~0x14
    if case % 16 in (0, 1, 2):
        flags |= (4, 0x10, 0x14)[case % 16]
    t.w8(wave + 0x18, flags)
    t.w32(wave + 0x20, rng.choice(STATES))
    t.w32(wave + 0x24, rng.choice((0, *voices)))
    t.w32(wave + 0x28, instances[0])
    t.w32(wave + 0x30, REQUESTS[case % len(REQUESTS)])
    t.w32(wave + 0x34, rng.choice(REQUESTS))
    t.w32(wave + 0x3c, rng.choice((0, *retained)))
    t.w32(wave + 0x44, rng.choice(STATES))
    t.w32(wave + 0x48, instances[1])
    t.w32(wave + 0x4c, rng.choice((0, *retained)))

    # Directed completion cases avoid starving the nested path behind the
    # stop requests, state checks, HRESULT, completion and high flag bit.
    if case % 8 in (3, 7):
        t.w8(wave + 0x18, flags & ~0x14)
        t.w32(wave + 0x30, 0)
        t.w32(wave + 0x34, 0)
        t.w32(wave + 0x20, rng.choice((3, 4)))
        t.w32(wave + 0x24, voices[0])
        t.w32(voices[0] + 8, rng.choice((0, 1, 0x80000000, 0xffffffff)))
        t.w32(voices[0] + 12, rng.choice((0, 1, 2, 0x100)))
        t.w8(voices[0] + 16, rng.choice((0, 0x80)))
    # Independent null-instance cases on paths that cannot detach an object.
    if case % 8 == 6:
        t.w32(wave + 0x28, 0)
        t.w32(wave + 0x3c, 0)
        t.w32(wave + 0x48, 0)
        t.w32(wave + 0x4c, 0)
        if case % 32 in (22, 30):
            t.w8(wave + 0x18, 0)
            t.w32(wave + 0x30, 1 if case % 32 == 22 else 2)
            t.w32(wave + 0x20, rng.choice((2, 3, 4, 6)))
    t.args(r3=wave)
