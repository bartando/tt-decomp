"""Stroke fan topology, caps, half-width rounding and stream completion.

Both dominant axes/directions, equal deltas, coincident endpoints, zero/negative
widths, subnormals, infinities and unordered comparisons. Begin changes render
state; the original offset helpers and vertex writer execute on both sides.
See _swf_line_inputs for supported memory and float-comparison limits.
"""
import struct
from liftcheck.spec import *
from specs._swf_line_inputs import SPECIAL, begin, stream, value

FUNCTION = "rage::swfDrawLine"
ADDRESS = 0x82406778
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
RET = None
CALLS = {
    0x82152A78: model(begin, args=("r3", "r4")),
    0x82406620: run(args=("f1", "f2", "f3")),
    0x824066C8: run(args=("f1", "f2", "f3")),
    0x82406010: run(args=("f1", "f2")),
}


def inputs(t):
    stream(t)
    r = t.rng
    x, y = value(r), value(r)
    dx, dy = r.choice(((20, 1), (-20, 1), (1, 20), (1, -20),
                       (20, 20), (-20, 20), (0, 0), (0, 20),
                       (20, 0), (value(r), value(r))))
    args = [x, y, x + dx, y + dy, value(r)]
    if r.randrange(3) == 0:
        args[r.randrange(5)] = struct.unpack(">f", struct.pack(">I", r.choice(SPECIAL)))[0]
    t.args(**{f"f{i + 1}": v for i, v in enumerate(args)})
