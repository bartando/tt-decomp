"""Store exactly one float at +0x48, retaining every neighboring byte."""
import struct
from liftcheck.spec import *

FUNCTION = "set_3348"
ADDRESS = 0x82483348
SOURCE = "src/physics/ph_float_property.cpp"
TRIALS = 256

def inputs(t):
    obj = t.alloc(128, "property")
    bits = [0, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC00042,
            1, 0x7F7FFFFF][t.index % 7] if t.index < 7 else t.rng.getrandbits(32)
    value = struct.unpack(">f", struct.pack(">I", bits))[0]
    t.args(r3=obj, f1=value)
