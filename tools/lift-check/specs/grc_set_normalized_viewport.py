"""Normalized viewport conversion, depth inversion and unconditional device call.

Independent signed dimensions (including >2^24 conversion rounding), negative
and fractional coordinates, both chip-ID branches and null/non-null devices.
All 24 viewport bytes at the call compare, as do device identity and all input
memory. Coordinates keep float-to-int conversion in range. Depth includes
signed zeros and out-of-range finite values. No GPU emulation, NaN/overflow
conversion, ignored writes or tolerance; the device callback alone is stubbed.
"""
from liftcheck.spec import *

FUNCTION = "grcSetNormalizedViewport"
ADDRESS = 0x8214EB10
SOURCE = "src/graphics/grc_gpu_resources.cpp"
TRIALS = 1000
CALLS = {"grcDevice_SetViewport": stub(ret="void", args=("r3", "r4"),
                                       deref={"r4": 24}, auto_out=False)}


def inputs(t):
    r = t.rng
    viewport = t.alloc(40, "viewportAndGuards") + 8
    dimensions = [0, 1, -1, 640, 720, 1280, 1920, -1080, 16777217, -16777217]
    for address in (0x825C9014, 0x825C9018):
        t.w32(address, r.choice(dimensions + [r.randrange(-100000, 100001)]))
    t.w32(0x825C9030, r.choice([0x1A220197, 0x1A220197, 0, 0x1A220196, t.u32()]))
    device = r.choice([0, t.alloc(16, "device")])
    t.w32(0x825EB988, device)
    for i in range(4):
        t.wf32(viewport + 4 * i, r.choice([0, -0.0, 1, -1, 0.5, 1.5, r.uniform(-4, 4)]))
    for i in (4, 5):
        t.wf32(viewport + 4 * i, r.choice([0, -0.0, 1, -1, 0.25, 0.75, r.uniform(-2, 2)]))
    t.args(r3=viewport)
