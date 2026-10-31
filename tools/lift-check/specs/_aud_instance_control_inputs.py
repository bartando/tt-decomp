"""Voice status and a callback replacing the instance's backend voice."""
from liftcheck.spec import *


def poll(c):
    voice = c.r(3)
    c.write(c.r(4), c.read(voice + 4, 4))
    instance = int.from_bytes(c.read(voice + 8, 4), "big")
    c.write(instance, c.read(voice + 12, 4))


CALLS = {"voice.vfn_2": model(poll, args=("r3",)),
         "voice.vfn_11": stub(ret="void", args=("r3", "r4")),
         "voice.vfn_1": stub(ret="void", args=("r3", "r4"))}


def inputs(t):
    rng = t.rng
    instance = t.alloc(256, "instance")
    voice = t.alloc(16, "voice")
    replacement = t.alloc(16, "replacementVoice")
    table = t.vtable("voice")
    t.w32(voice, table)
    t.w32(replacement, table)
    t.w32(voice + 4, rng.choice((0, 4, 8, 0x10, 0x20, 0x30, 0x40, 0xffffffff)))
    t.w32(voice + 8, instance)
    t.w32(voice + 12, rng.choice((voice, replacement)))
    t.w32(instance, voice if rng.randrange(8) else 0)
    t.args(r3=instance)
