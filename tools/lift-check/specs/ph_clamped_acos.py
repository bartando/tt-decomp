"""0x8227DD20: endpoint saturation and unordered saturation and the double CRT call for interior inputs."""
import math
import struct
from liftcheck.spec import *

FUNCTION = "phBoundCapsule_DD20_fw"
ADDRESS = 0x8227DD20
SOURCE = "src/rage/math/ph_math.cpp"
TRIALS = 1000
CALLS = {"crt_acos": model(lambda c: c.ret(f1=math.acos(c.f(1))), args=("f1",))}


def inputs(t):
    bits = t.rng.choice([0, 0x80000000, 0x3F800000, 0xBF800000,
                         0x3F7FFFFF, 0xBF7FFFFF, 0x3F800001, 0xBF800001,
                         0x7F800000, 0xFF800000, 0x7FC00001, 0xFFC00001,
                         t.rng.getrandbits(32)])
    value = struct.unpack(">f", struct.pack(">I", bits))[0]
    t.args(f1=value)
