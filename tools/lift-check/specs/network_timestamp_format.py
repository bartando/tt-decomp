"""0x8239BF30: signed minute/second formatting and fctidz low-word saturation."""
from liftcheck.spec import *
FUNCTION = "FormatTimestampForLog"
ADDRESS = 0x8239BF30
SOURCE = "src/game/network/network_timestamp.cpp"
TRIALS = 600
CALLS = {"_snprintf": stub(args=('r3','r4','r5','r6','r7','r8'), deref={'r5': 15})}
def inputs(t):
    timestamp = t.alloc(8, 'timestamp')
    t.w32(timestamp, t.rng.choice([0,1,59,60,61,0xFFFFFFFF,0x80000000,0x7FFFFFFF,t.u32()]))
    if t.index % 2:
        t.w32(timestamp + 4, t.rng.choice([0x7F800000,0xFF800000,0x7FC00000,0x5F000000,0xDF000000,t.u32()]))
    else:
        t.wf32(timestamp + 4, t.rng.uniform(-2,2))
    t.args(r3=timestamp)
