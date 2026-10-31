"""0x8225E408: decode all message-target flags, diagnostic uses only r4's byte."""
from liftcheck.spec import *
FUNCTION = "GetPlayerID"
ADDRESS = 0x8225E408
SOURCE = "src/game/network/pong_network_io.cpp"
TRIALS = 512
CALLS = {"nop_8240E6D0": stub(ret="void", args=("r3",), deref={"r3": 37})}
def inputs(t):
    message = t.alloc(16, "message")
    t.w8(message + 2, t.index % 256)
    t.args(r3=message, r4=t.rng.choice([0, 1, 255, 256, 0xFFFFFF00, t.u32()]))
