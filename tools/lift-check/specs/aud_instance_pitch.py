"""Full variable index forwarding, low-half sentinel, voice reload, FP bits."""
from liftcheck.spec import *

FUNCTION = "rage::aud_FD10"
ADDRESS = 0x821AFD10
SOURCE = "src/rage/audio/aud_instance_update.cpp"
TRIALS = 400


def index(c):
    voice = c.r(3)
    instance = int.from_bytes(c.read(voice + 8, 4), "big")
    c.write(instance, c.read(voice + 12, 4))
    c.ret(r3=int.from_bytes(c.read(voice + 4, 4), "big"))


CALLS = {"voice.vfn_8": model(index, args=("r3", "r4")),
         "voice.vfn_9": stub(ret="void", args=("r3", "r4", "f1"))}


def inputs(t):
    rng = t.rng
    instance = t.alloc(256, "instance")
    voice = t.alloc(16, "voice")
    replacement = t.alloc(16, "replacementVoice")
    table = t.vtable("voice")
    t.w32(voice, table)
    t.w32(replacement, table)
    t.w32(voice + 4, rng.choice((0, 1, 0xffff, 0x1234ffff, 0xffff1234, 0xffffffff, rng.getrandbits(32))))
    t.w32(voice + 8, instance)
    t.w32(voice + 12, rng.choice((voice, replacement)))
    t.w32(instance, voice if rng.randrange(8) else 0)
    t.args(r3=instance, f1=rng.choice((0.0, -0.0, 1.0, -1.0, float("inf"),
                                     -float("inf"), float("nan"), rng.uniform(-1e6, 1e6))))
