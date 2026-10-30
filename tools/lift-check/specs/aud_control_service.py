"""Playback transitions and dirty propagation, including callee side effects."""
import struct
from liftcheck.spec import *

FUNCTION = "rage::audControl::Service"
ADDRESS = 0x82161700
SOURCE = "src/rage/audio/rage_audio.cpp"
TRIALS = 1200


def playing(ctx):
    result, owner, replace, replacement = struct.unpack(">IIII", ctx.read(ctx.r(3) + 4, 16))
    if replace:
        ctx.write(owner + 4, struct.pack(">I", replacement))
    ctx.ret(r3=result)


def stop(ctx):
    owner = ctx.r(3)
    replacement, flags = struct.unpack(">II", ctx.read(owner + 80, 8))
    ctx.write(owner + 4, struct.pack(">I", replacement))
    ctx.write(owner + 16, bytes(4))
    ctx.write(owner + 20, struct.pack(">I", flags))


def release(ctx):
    owner = struct.unpack(">I", ctx.read(ctx.r(3) + 8, 4))[0]
    # The release callback may repopulate the voice; Service still clears it.
    ctx.write(owner + 4, struct.pack(">I", ctx.r(3)))


def update(ctx):
    # Observe r4 as well as the dirty word before the unconditional clear.
    ctx.write(ctx.r(3) + 20, b"\x80\x00\x00\x00")


CALLS = {
    "voice.vfn_18": model(playing, args=("r3",)),
    "voice.vfn_8": model(release, args=("r3",)),
    "control.vfn_4": model(stop, args=("r3",)),
    "control.vfn_7": model(update, args=("r3", "r4"), deref={"r3": 24}),
}


def inputs(t):
    rng = t.rng
    control = t.alloc(96, "control")
    group = t.alloc(48, "group")
    voices = [t.alloc(24, f"voice {i}") for i in range(2)]
    t.w32(control, t.vtable("control", 20))
    vt = t.vtable("voice", 20)
    for voice in voices:
        t.w32(voice, vt)
        t.w32(voice + 4, rng.choice([0, 1, 2, 0x80, 0xff, 0x100, 0xffffff00]))
        t.w32(voice + 8, control)
        t.w32(voice + 12, rng.choice([0, 0, 1]))
        t.w32(voice + 16, voices[1])
    t.w32(control + 4, rng.choice([0, *voices, *voices]))
    t.w32(control + 12, group)
    t.w32(control + 16, rng.choice([0, 1, 1, 2, 2, 3, 3, 4, -1, 0x80000000]))
    t.w32(control + 20, rng.choice([0, 0, 1, 2, 4, 8, 16, 32, 0x80000000, rng.getrandbits(32)]))
    t.w32(control + 80, rng.choice([0, *voices]))
    t.w32(control + 84, rng.choice([0, 0, 2, 0x80000000, rng.getrandbits(32)]))
    t.w32(group + 40, rng.choice([0, 0, 1, 2, 4, 8, 16, 32, 64, 0x80000000, rng.getrandbits(32)]))
    t.w8(0x82606418, rng.choice([0, 0, 1, 2, 0x80, 0xff]))
    t.args(r3=control)
