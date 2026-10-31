"""0x823EDDB8: head/tail/interior removal, detached guard and count wrap."""
from liftcheck.spec import *
FUNCTION='rage::snSession_States::snSession_RemoveConnectionNode'
ADDRESS=0x823EDDB8
SOURCE='src/rage/network/hsm_transition.cpp'
TRIALS=600
def inputs(t):
    context=t.alloc(128,'context')
    node=t.alloc(24,'node')
    previous=t.alloc(24,'previous') if t.rng.randrange(2) else 0
    next=t.alloc(24,'successor') if t.rng.randrange(2) else 0
    t.w32(node+4,previous)
    t.w32(node+8,next)
    t.w32(context+0x5C,previous or node)
    t.w32(context+0x60,next or node)
    t.w32(context+0x64,t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
    t.args(r3=context,r4=t.rng.choice([0,node,node,node]))
