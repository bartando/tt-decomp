"""0x823ED418: strict common ancestors, equal states and disjoint trees."""
from liftcheck.spec import *
FUNCTION='snSession_D418_w'
ADDRESS=0x823ED418
SOURCE='src/rage/network/hsm_transition.cpp'
TRIALS=1200
def inputs(t):
    states=[t.alloc(24,'state') for _ in range(24)]
    for i,state in enumerate(states): t.w32(state+8,t.rng.choice([0]+states[:i]))
    left=t.rng.choice(states)
    right=t.rng.choice([left]+states)
    t.args(r3=left,r4=right)
