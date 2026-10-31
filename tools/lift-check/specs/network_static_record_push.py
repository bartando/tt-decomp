"""0x825821A8: link the actual static registry record, preserving its name/index.
Getter is a call boundary; all holder/record writes and count wrap are compared.
"""
from liftcheck.spec import *
FUNCTION = "pongNetMessageHolder_21A8_2h"
ADDRESS = 0x825821A8
SOURCE = "src/game/network/pong_network.cpp"
TRIALS = 1000
CALLS = {"pongNetMessageHolder_FAE0_isl": stub(ret=0x45000000, args=())}
def inputs(t):
    holder=t.map(0x45000000,0x1000,'holder')
    t.w32(holder+8,t.u32())
    t.w32(holder+12,t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
