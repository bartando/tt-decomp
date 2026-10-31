"""0x824566B0: all gate combinations, completion virtual and signed deadlines."""
from specs._network_sink_deadline_cases import *
FUNCTION='msgSink_IsPeerReady'
ADDRESS=0x824566B0
SOURCE='src/game/network/msg_sink_timing.cpp'
TRIALS=1600
CALLS={**CALLS,'msgSink_GetAdjustedDeadlineOverrun':run(),
       'msgSink_HasCompletedSession':run(),
       'target.vfn_12':stub(ret=lambda c:c.rng.choice([0,255,511,256,0xFFFFFFFF]))}
def inputs(t):
    sink=make_sink(t)
    context=t.alloc(64,'context')
    info=t.alloc(32,'peer info')
    primary=make_peer(t,96)
    secondary=t.alloc(96,'secondary')
    tertiary=t.alloc(96,'tertiary')
    t.w32(sink+0x38,context)
    t.w32(sink+0x198,info)
    t.w32(sink+0x190,t.rng.choice([0,0,0,0,primary]))
    t.w32(sink+0x158,t.rng.choice([8,8,1,t.u32()]))
    t.w32(sink+0x3C,t.rng.choice([0,1,t.u32()]))
    t.w32(sink+0x19C,t.rng.choice([1,1,1,1,0,t.u32()]))
    t.w32(sink+0x17C,t.rng.choice([0,0,0,0,1,t.u32()]))
    t.w32(sink+0x178,t.rng.choice([0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF,t.u32()]))
    t.w32(sink+0x184,t.rng.choice([0,0,1,t.u32()]))
    t.w32(context+0x28,t.u32())
    t.w16(info+0x18,t.rng.randrange(65536))
    for offset,obj in [(0x34,primary),(0x18C,secondary),(0x188,tertiary)]:
        t.w32(sink+offset,t.rng.choice([0,0,obj,obj]))
        t.w32(obj+0x50,t.rng.choice([0,3,3,3,5,6,t.u32()]))
    t.args(r3=sink)
