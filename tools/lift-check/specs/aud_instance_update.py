"""Voice polling, state transitions and spatial updates at 0x821AFD90."""
from liftcheck.spec import *

FUNCTION = "rage::audInstance_Update"
ADDRESS = 0x821AFD90
SOURCE = "src/rage/audio/aud_instance_update.cpp"
RET = None


def poll(ctx):
    voice = ctx.r(3)
    ctx.write(ctx.r(4), ctx.read(voice + 4, 4))
    if int.from_bytes(ctx.read(voice + 12, 4), "big"):
        ctx.write(int.from_bytes(ctx.read(voice + 8, 4), "big"), bytes(4))


CALLS = {
    "voice.vfn_2": model(poll, args=("r3",)),
    "voice.vfn_3": stub(ret="void", args=("r3",)),
    "voice.vfn_8": stub(ret=0x1234, args=("r3", "r4")),
    "voice.vfn_9": stub(ret="void", args=("r3", "r4", "f1")),
    0x82481920: stub(ret="void", args=("r3", "r4", "r5", "r6")),
    0x821AF860: stub(ret="void", args=("r3",)),
}


def inputs(t):
    rng = t.rng
    instance = t.alloc(256, "instance")
    voice = t.alloc(16, "voice")
    t.w32(voice, t.vtable("voice"))
    flags = rng.choice([0, 4, 0x20, 0x24, 0xffffffff, 1])
    t.w32(voice + 4, flags)
    t.w32(voice + 8, instance)
    # Only clear the voice during polling when the stopped bit is set.
    t.w32(voice + 12, rng.randrange(2) if flags & 0x20 else 0)
    t.w32(instance, voice if rng.randrange(8) else 0)
    t.w8(instance + 4, rng.choice([14, 14, 0, 15, 19, 255]))
    t.w8(instance + 5, rng.choice([0, 1, 2, 255]))
    t.w8(instance + 6, rng.choice([0, 1, 2, 255]))
    t.wf32(instance + 252, rng.uniform(-100, 100))
    t.args(r3=instance)


if __name__ == "__main__":
    from pathlib import Path
    from liftcheck.runner import Checker, Options

    mutations = {
        "wrong playing flag": ("flags & 4", "flags & 8"),
        "wrong transition state": ("instance->state = 15", "instance->state = 16"),
        "wrong stopped flag": ("flags & 0x20", "flags & 0x40"),
        "reversed persistence state": ("instance->persistent ? 11 : 19", "instance->persistent ? 19 : 11"),
        "wrong voice release argument": ("table[3])(voice)", "table[3])(nullptr)"),
        "wrong spatial mask": ("spatialInput, 61,", "spatialInput, 60,"),
        "wrong distance": ("parameter, instance->distance", "parameter, 0.0f"),
        "skip parameter update": ("audInstance_UpdateParameters(instance);", "(void)instance;"),
    }
    for name, patch in mutations.items():
        print(f"Mutation: {name}", flush=True)
        result = Checker(Path(__file__), Options(trials=128, seed=1, patches=(patch,))).run()
        assert result == 1, f"mutation must FAIL, got exit {result}: {name}"
