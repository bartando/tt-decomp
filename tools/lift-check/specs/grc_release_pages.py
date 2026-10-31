"""Packed cache range endpoints, page-count wrap, sentinels and callback edits.
Cache maintenance itself is a boundary; its endpoints, call order, resource
writes and final sync are compared exactly. No memory is ignored.
"""
from liftcheck.spec import *
FUNCTION = 'grc_2CC8'
ADDRESS = 0x82352CC8
SOURCE = 'src/graphics/grc_resource_release.cpp'
TRIALS = 1000
CACHE_EFFECTS = True
_resource=0
_mutate=False

def flush(c):
    c.rec.derefs['resource'] = (c.read(_resource,16),None)
    if _mutate:
        c.write(_resource,c.rng.getrandbits(32).to_bytes(4,'big'))
        c.write(_resource+12,c.rng.choice([0xFFFF0000,c.rng.getrandbits(32)]).to_bytes(4,'big'))
    c.ret()

CALLS={'rage_EEC0':model(flush,args=('r3','r4'))}
def inputs(t):
    global _resource,_mutate
    _resource=t.alloc(48,'resourceAndGuards')+16
    _mutate=t.index%3==0
    flags=(t.u32() & ~0xF000) | t.rng.choice([0,0x1000,0x1000,0x2000,0xF000])
    t.w32(_resource,flags)
    for off in [8,12]: t.w32(_resource+off,t.rng.choice([0xFFFF0000,0,t.u32()]))
    t.args(r3=_resource,r4=t.u32(),r5=t.rng.choice([0,t.u32()]))
