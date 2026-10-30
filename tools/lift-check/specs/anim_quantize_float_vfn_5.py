from liftcheck.spec import *

FUNCTION = "rage::crAnimChannelQuantizeFloat::vfn_5"
ADDRESS = 0x822478E0
SOURCE = "src/rage/animation/rage_anim.cpp"
CALLS = {"rage::AnimFloor": run(), "rage::DecodeQuantizedFloat": run()}
RET = None

# Finite, representable animation times and nonempty sample arrays; exceptional
# float-to-integer conversions and malformed channels are outside this spec.
def inputs(t):
    channel = t.alloc(24, "channel", fill="zero")
    count = t.rng.randint(1, 32)
    samples = t.alloc(count * 2, "samples")
    for i in range(count):
        t.w16(samples + 2 * i, t.rng.randrange(65536))
    t.w32(channel + 8, samples)
    t.w16(channel + 12, count)
    t.wf32(channel + 16, t.rng.uniform(-100, 100))
    t.wf32(channel + 20, t.rng.uniform(-100, 100))
    out = t.alloc(4, "out")
    t.wf32(out, 0.0)
    frame = t.rng.randint(-10, count + 10)
    fraction = t.rng.choice([0.0, 0.0005, 0.001, 0.0011, 0.5, 0.9989, 0.999, 0.9995, t.rng.random()])
    t.args(r3=channel, r4=0, r5=out, f1=frame + fraction)
