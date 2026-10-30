"""Case folding, signed bytes, empty strings, and repeated hash avalanche."""
from liftcheck.spec import *

FUNCTION = "swfHashMemberName"
ADDRESS = 0x8223A868
SOURCE = "src/rage/swf_clip_events.cpp"
TRIALS = 1000


def inputs(t):
    r = t.rng
    samples = [b'', b'a', b'z', b'AZaz', b'longMemberName123456789', bytes([0x80, 0xff, 0x7f])]
    if r.randrange(2):
        data = bytes(r.randrange(1, 256) for _ in range(r.randrange(1, 100)))
    else:
        data = r.choice(samples)
    s = t.alloc(len(data) + 1, 'name', fill=data + b'\0')
    t.args(r3=s)
