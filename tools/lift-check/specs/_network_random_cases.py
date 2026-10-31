from liftcheck.spec import *
SOURCE='src/rage/math/random_range.cpp'
TRIALS=1000
EXTERNS={'rage::g_randomShuffleTable':0x825BD5B0}
CALLS={'rage::randomNext':run()}
def setup_random(t):
    owner=t.alloc(0xB0,'random owner')
    t.w32(owner+0xAC,t.rng.choice([0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF,t.u32()]))
    for i in range(128): t.w32(0x825BD5B0+i*4,t.u32())
    return owner
def range_inputs(t):
    owner=setup_random(t)
    low=t.rng.choice([0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF,t.u32()])
    high=t.rng.choice([low,low,0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF,t.u32()])
    if (high-low+1)&0xFFFFFFFF==0: high=low
    t.args(r3=owner,r4=low,r5=high)
