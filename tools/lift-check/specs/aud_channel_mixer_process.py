"""0x82465550: planar 256-sample audio mixing, formerly ph_vt58FC_13_5550.

Runs the real buffer descriptor helpers. Covers routed/identity maps, zero and
unequal channel counts, invalid route indices, duplicate destinations, gain
ramps, add/overwrite (including noncanonical nonzero flags), in-place/overlapping
sample storage, output-resize failure, and recursive/contended/unowned locks.
VMX subnormals, signed zeros, infinities and NaNs are included; FTOL=0, no ignored
memory. Kernel operations and the two byte-copy/fill routines are modeled.

Limits: valid aligned storage for all referenced channels, at most four channels
and eight routes, 48 kHz buffers. This checks the lift-check VMX model, not real
Xenon NaN payloads or hardware rounding. The descriptor getter always succeeds
in the original, so its defensive negative-status exits are unreachable here.

Run this file directly with the lift-check Python environment/PYTHONPATH to run
the deliberate mutation checks as well; each mutation must report FAIL.
"""

from liftcheck.spec import *

FUNCTION = "rage::audChannelMixer_Process"
ADDRESS = 0x82465550
SOURCE = "src/rage/audio/aud_channel_mixer.cpp"
FP_CONTRACT = "off"
TRIALS = 512

LOCK = 0x825E7870
TLS = 0x7D000000


def _acquire(ctx):
    assert ctx.r(3) == LOCK
    # A contending owner has finished releasing before acquisition returns.
    ctx.write(LOCK, (1).to_bytes(4, "big") + bytes(4))


def _release(ctx):
    assert ctx.r(3) == LOCK
    assert ctx.read(LOCK + 4, 9) == bytes(9)
    ctx.write(LOCK, bytes(4))


def _copy(ctx):
    destination, source, size = ctx.r(3), ctx.r(4), ctx.r(5)
    assert size == 1024
    ctx.write(destination, ctx.read(source, size))
    ctx.ret(r3=destination)


def _fill(ctx):
    destination, value, size = ctx.r(3), ctx.r(4), ctx.r(5)
    assert value == 0 and size == 1024
    ctx.write(destination, bytes(size))
    ctx.ret(r3=destination)


CALLS = {
    0x82465D80: run(),
    0x82465EF0: run(),
    0x8258653C: stub(ret=1, args=()),
    0x8258634C: model(_acquire, args=("r3",)),
    0x8258631C: model(_release, args=("r3",)),
    0x8258654C: stub(ret="void", args=("r3",)),
    0x82568680: model(_copy, args=("r3", "r4", "r5"), deref={"r4": 1024}),
    0x82566898: model(_fill, args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    source_count = rng.randrange(5)
    destination_count = rng.randrange(5)
    overwrite = rng.choice([0, 0, 1, 1, 2, 255])
    output_count = rng.randrange(6)  # 5 exceeds the four-channel capacity
    route_count = rng.choice([0, 0, 1, 2, 4, 8])
    alias = rng.randrange(5)

    # Include a vector offset overlap and shared sample storage with distinct
    # interface pointers. Only equal interface pointers skip the identity map.
    storage = t.alloc(4 * 1024 + 16, "sourceSamples")
    output = t.alloc(4 * 1024 + 16, "destinationSamples") if alias < 2 else storage + (16 if alias == 2 else 0)
    special = [0.0, -0.0, 2.0**-149, -(2.0**-149), 2.0**-126,
               float("inf"), -float("inf"), float("nan")]
    for base in dict.fromkeys([storage, output]):
        for sample in range(1024):
            value = rng.choice(special) if rng.random() < 0.08 else rng.uniform(-2, 2)
            t.wf32(base + sample * 4, value)

    def buffer(name, channels, samples):
        owner = t.alloc(0x24, name)
        t.w8(owner + 0x0D, 4)             # capacity in channels at 48 kHz
        t.w32(owner + 0x10, 48000)
        t.w8(owner + 0x14, 0)             # float PCM descriptor
        t.w8(owner + 0x15, channels)
        t.w32(owner + 0x18, 48000)
        t.w32(owner + 0x1C, samples)
        return owner + 8

    source = buffer("sourceBuffer", source_count, storage)
    destination = source if alias == 4 else buffer("destinationBuffer", destination_count, output)
    mixer = t.alloc(28, "mixer")
    routes = t.alloc(12 * max(route_count, 1), "routes")
    t.w8(mixer + 16, route_count)
    t.w32(mixer + 20, routes)
    t.w8(mixer + 25, output_count)
    t.w8(mixer + 26, overwrite)
    gains = [-2.0, -0.0, 0.0, 0.5, 1.0, 2.0, 2.0**-140,
             -2.0**-140, float("nan"), float("inf"), -float("inf")]
    for i in range(route_count):
        route = routes + 12 * i
        t.w8(route, rng.choice([0, 1, 2, 3, 4, 255]))
        t.w8(route + 1, rng.choice([0, 1, 2, 3, 4, 255]))
        current = rng.choice(gains) if rng.random() < 0.4 else rng.uniform(-2, 2)
        target = rng.choice(gains) if rng.random() < 0.4 else rng.uniform(-2, 2)
        t.wf32(route + 4, current)
        t.wf32(route + 8, target)

    depth = rng.choice([0, 0, 1, 2, 7])
    owner = rng.choice([TLS, TLS, 0x12345678])
    t.w32(LOCK, 1 if depth else 0)
    t.w32(LOCK + 4, depth)
    t.w32(LOCK + 8, owner)
    t.w8(LOCK + 12, rng.randrange(4))
    t.args(r3=mixer, r4=source, r5=destination)


if __name__ == "__main__":
    from pathlib import Path
    from liftcheck.runner import Checker, Options

    mutations = {
        "wrong gain ramp divisor": ("difference * (1.0f / 256.0f)", "difference * (1.0f / 128.0f)"),
        "missing final sample group": ("group < 64", "group < 63"),
        "add instead of overwrite": ("if (mixer->overwrite == 0)", "if (true)"),
        "accept out-of-range destination": ("route.destination >= destination.channels",
                                            "route.destination > destination.channels"),
        "missing gain commit": ("route.currentGain = target;", "route.currentGain = 0.0f;"),
        "missing recursive unlock": ("if (--lock.depth == 0)", "if (lock.depth == 0)"),
        "missing VMX flush": ("if ((bits & 0x7F800000u) == 0)", "if (false)"),
        "overwrite flag tested as boolean": ("if (mixer->overwrite == 1)", "if (mixer->overwrite != 0)"),
    }
    for name, patch in mutations.items():
        print(f"Mutation: {name}", flush=True)
        result = Checker(Path(__file__), Options(trials=128, seed=1, patches=(patch,))).run()
        assert result == 1, f"mutation must FAIL, got exit {result}: {name}"
