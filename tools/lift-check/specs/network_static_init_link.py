"""0x825808B0: init-list linkage and destructor registration. This uses an init
link at +4, a distinct layout from the named static records used by 21A8/2228.
"""
from liftcheck.spec import *
FUNCTION = "pongNetMessageHolder_08B0_p"
ADDRESS = 0x825808B0
SOURCE = "src/game/network/pong_network.cpp"
TRIALS = 1000
CALLS = {0x8242F7D0: stub(ret=0, args=("r3",))}
def inputs(t):
    t.w32(0x826066A0,t.u32())
    t.w32(0x826066A4,t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
