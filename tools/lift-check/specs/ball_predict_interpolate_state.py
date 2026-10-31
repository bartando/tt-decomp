"""Live/previous prediction blending: low-byte gate, sequential snapshots,
reloaded bank pointers and the NaN-safe fsel clamp."""
import struct
from liftcheck.spec import *

FUNCTION = "BallPredict_InterpolateState"
ADDRESS = 0x821D3C60
SOURCE = "src/game/ball/ball_prediction_stream.cpp"
TRIALS = 1200


def u32(c, p):
    return struct.unpack(">I", c.read(p, 4))[0]


def w32(c, p, v):
    c.write(p, struct.pack(">I", v & 0xffffffff))


def should(c):
    state = c.r(3)
    w32(c, state + 0x14, u32(c, state + 0x18))
    c.ret(r3=u32(c, state))


def cache(c):
    script = u32(c, c.r(3))
    state, sample, replacement, live, previous = struct.unpack(">5I", c.read(script, 20))
    if not previous:
        w32(c, state + 0x10, replacement)
    else:
        # The first result has to have been copied before the second lookup.
        c.write(live, bytes([0x42]) * 0x50)
    c.ret(r3=sample)


def copy_fields(c, destination, source):
    for off, size in ((0, 11), (0x10, 0x40)):
        c.write(destination + off, c.read(source + off, size))


def direct(c):
    script = u32(c, c.r(3))
    sample = u32(c, script + 4)
    copy_fields(c, c.r(5), sample)


def transition(c):
    # Observe every initialized field of both stack snapshots, without assigning
    # meaning to their padding or duplicating the transition-blend math.
    copy_fields(c, c.r(3), c.r(5))
    copy_fields(c, c.r(3) + 0x50, c.r(6))


CALLS = {
    "BallPredict_ShouldUsePrevious": model(should, args=("r3",), preserves=("f1",)),
    "BallPredict_GetInterpolatedSample": model(cache, args=("r3", "f1")),
    "BallPredict_InterpolateSamples": model(direct, args=("r3", "r5", "f1")),
    "BallPredict_BlendTransitionSamples": model(transition, args=("r3", "f1")),
}


def inputs(t):
    rng = t.rng
    state = t.alloc(0x30, "transition state")
    samples = [t.alloc(0x50, f"sample{i}", ctype="gdBallPredictSample") for i in range(4)]
    for sample in samples:
        t.floats(sample, 2, -10, 10)
        t.floats(sample + 0x10, 16, -10, 10)
        for off in (8, 9, 10):
            t.w8(sample + off, rng.choice([0, 1, 2, 0x80, 0xff]))
    banks = [t.alloc(0x40, f"bank{i}") for i in range(4)]
    for i, bank in enumerate(banks):
        script = t.alloc(20, f"bank script{i}")
        t.w32(bank + 0x20, script)
        for off, value in enumerate([state, samples[i], banks[2], samples[3], i == 2]):
            t.w32(script + off * 4, int(value))
    # The predicate replaces the live bank; its cache lookup then replaces the
    # previous bank. The two initial pointers are deliberate decoys.
    t.w32(state + 0x10, banks[0])
    t.w32(state + 0x14, banks[1])
    t.w32(state + 0x18, banks[3])
    t.w32(state, rng.choice([0, 1, 0x100, 0x101, 0x10000, 0x12340001, 0xffffffff]))
    t.wf32(state + 4, rng.uniform(-5, 5))
    rate = rng.choice([-2., -1., -0., 0., 0.25, 1., 2., float("nan"), float("inf")])
    hit_time = rng.choice([-1., 0., 1.])
    query = [-2., -0., 0., 0.25, 0.5, 1., 2., float("nan"), float("inf"), -float("inf")][t.index % 10]
    t.wf32(state + 8, rate)
    t.wf32(state + 12, hit_time)
    out = t.alloc(0xA0, "observed transition snapshots")
    t.mark_type(out, "gdBallPredictSample")
    t.mark_type(out + 0x50, "gdBallPredictSample")
    t.args(r3=state, r4=rng.getrandbits(32), r5=out, f1=query)
