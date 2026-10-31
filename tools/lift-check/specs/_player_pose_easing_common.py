import math
import struct
from liftcheck.spec import *

SOURCE = "src/game/player/player_pose_easing.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
CALLS = {
    "crt_sin": model(lambda c: c.ret(f1=math.sin(c.f(1))), args=("f1",)),
    "crt_cos": model(lambda c: c.ret(f1=math.cos(c.f(1))), args=("f1",)),
}


def inputs(t):
    choice = t.index % 5
    value = t.rng.choice([-1.0, -0.0, 0.0, 1.0, 2.0, float("nan"), float("inf"), -float("inf")])
    if choice == 1:
        value = struct.unpack(">f", struct.pack(">I", t.rng.getrandbits(32)))[0]
    elif choice in (2, 3):
        value = t.rng.random()
    value = struct.unpack(">f", struct.pack(">f", value))[0]
    t.args(f1=value)
