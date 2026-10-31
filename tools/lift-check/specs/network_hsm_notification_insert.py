"""0x823EDD10: detached flag, tail insertion and existing successor repair."""
from liftcheck.spec import *
FUNCTION='rage::snSession_States::snSession_InsertConnectionNode'
ADDRESS=0x823EDD10
SOURCE='src/rage/network/hsm_transition.cpp'
TRIALS=600
def inputs(t):
    context=t.alloc(128,'context')
    node=t.alloc(24,'node')
    previous=t.alloc(24,'previous')
    next=t.alloc(24,'successor')
    t.w32(context+0x5C,t.rng.choice([0,previous]))
    t.w32(context+0x60,previous)
    t.w32(context+0x64,t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
    t.w32(previous+8,t.rng.choice([0,next]))
    t.args(r3=context,r4=t.rng.choice([0,node,node,node]))
