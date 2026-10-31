"""0x82454158: absent delegation and low-byte 0xFF completion status."""
from specs._network_sink_deadline_cases import *
FUNCTION='msgSink_HasCompletedSession'
ADDRESS=0x82454158
SOURCE='src/game/network/msg_sink_timing.cpp'
TRIALS=600
CALLS={**CALLS,'target.vfn_12':stub(ret=lambda c:c.rng.choice([0,1,255,256,511,0xFFFFFFFF,c.rng.getrandbits(32)]))}
def inputs(t): t.args(r3=make_peer(t))
