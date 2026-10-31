"""Linear/radial sampling, inclusive stops, unsigned decreasing-channel math.

Stops are strictly increasing (a selected zero-width span traps in retail).
sqrt is a libm boundary model; other arithmetic and all return bits are exact.
"""
import math
from liftcheck.spec import *

FUNCTION = "rage::swfSampleGradient"
ADDRESS = 0x824060B8
SOURCE = "src/rage/swf_paint.cpp"
TRIALS = 800
EXTERNS = {"sqrt": 0x824301D0}
CALLS = {0x824301D0: model(lambda c: c.ret(f1=math.sqrt(c.f(1))), args=("f1",))}


def inputs(t):
    rng = t.rng
    gradient = t.alloc(36, "gradient")
    count = rng.choice((0, 1, 2, 3, 6, 12))
    stops = sorted(rng.sample(range(256), max(1, count)))
    if count >= 2 and rng.randrange(2):
        stops = [0] + sorted(rng.sample(range(1, 255), count - 2)) + [255]
    ratios = t.alloc(len(stops), "ratios", fill=bytes(stops))
    colors = t.alloc(max(1, count) * 4, "colors")
    for i in range(max(1, count)):
        t.w32(colors + i * 4, rng.choice((0, 0xffffffff, 0xff000000, 0x00ffffff, rng.getrandbits(32))))
    t.w8(gradient + 24, count)
    radial = rng.choice((0, 1, 2, 255))
    t.w8(gradient + 25, radial)
    t.w32(gradient + 28, ratios)
    t.w32(gradient + 32, colors)
    if t.index % 3 == 0:
        t.floats(gradient, 6, -3, 3)
        x, y = rng.uniform(-40000, 40000), rng.uniform(-40000, 40000)
    else:
        for i, value in enumerate((1, 0, 0, 1, 0, 0)):
            t.wf32(gradient + i * 4, value)
        target = rng.choice((*stops, 0, 255, -1, 256, rng.uniform(0, 255)))
        x = target / float.fromhex("0x1.fdfffep-7") if radial else target / float.fromhex("0x1.fep-8") - 16384
        y = 0.0
        if t.index % 17 == 0:
            x = rng.choice((float("nan"), float("inf"), -float("inf"), -0.0))
    t.args(r3=gradient, f1=x, f2=y)
