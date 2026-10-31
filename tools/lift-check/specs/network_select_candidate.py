"""0x8245AAC8: packed low-word count, inclusive float bounds and random owner."""
from liftcheck.spec import *
FUNCTION='pongNetMessageHolder_AAC8_w'
ADDRESS=0x8245AAC8
SOURCE='src/game/network/network_selection.cpp'
TRIALS=1000
def _allocate(c):
    c.ret(r3=0 if c.rng.randrange(5)==0 else c.alloc(max(1,c.r(3))))
CALLS={'rage_Alloc':model(_allocate,args=('r3',)),'rage_free':stub(ret='void',args=('r3',)),
       'rage::randomRangeInclusiveSigned':stub(ret=lambda c:c.rng.randrange(c.r(5)+1),args=('r3','r4','r5'))}
def inputs(t):
    owner=t.alloc(16,'holder')
    count=t.rng.randrange(25)
    inner=t.alloc(8+16*count,'candidate pool')
    random=t.alloc(0xB0,'random owner')
    slot=t.alloc(2,'slot')
    payload=t.alloc(4,'payload')
    t.w32(owner+4,random)
    t.w32(owner+8,inner)
    t.w32(inner,(t.rng.randrange(65536)<<16)|count)
    samples=[0.0,1.0,-1.0,float('inf'),-float('inf'),float('nan'),t.rng.uniform(-100,100)]
    value=t.rng.choice(samples)
    for i in range(count):
        t.wf32(inner+8+i*16+4,t.rng.choice(samples))
        t.wf32(inner+8+i*16+8,t.rng.choice(samples))
    t.args(r3=owner,r4=t.u32(),r5=slot,r6=payload,f1=value)
