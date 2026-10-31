"""PPC single-precision +/- half, then saturating fctiwz conversion."""
import struct
from liftcheck.spec import *

FUNCTION = "RoundHalfAwayFromZero"
ADDRESS = 0x8210CB88
SOURCE = "src/game/drill/pong_drill.cpp"
TRIALS = 1200


def inputs(t):
    edges = [0.0, -0.0, .5, -.5, 1.5, -1.5, .49999997, -.49999997,
             2147483520.0, 2147483648.0, -2147483648.0, -2147483904.0,
             float('inf'), -float('inf'), float('nan')]
    if t.index < len(edges):
        value = edges[t.index]
    elif t.index % 3 == 0:
        value = struct.unpack('>f', t.u32().to_bytes(4, 'big'))[0]
    else:
        value = t.rng.choice([t.rng.uniform(-1e5, 1e5), t.rng.randrange(-100, 100) + .5])
    t.args(f1=value)
