"""0x823DD170: append/insert notifier, retain payload, wire owner and wrap count."""
from liftcheck.spec import *
FUNCTION = "rage::snSession_States::snSession_RegisterNotifier"
ADDRESS = 0x823DD170
SOURCE = "src/rage/network/session_state_helpers.cpp"
TRIALS = 600
def inputs(t):
    owner=t.alloc(24,'owner')
    node=t.alloc(24,'notifier')
    previous=t.alloc(24,'previous')
    successor=t.alloc(24,'successor') if t.rng.randrange(2) else 0
    t.w32(owner+12,t.rng.choice([0,previous]))
    t.w32(owner+16,previous)
    t.w32(owner+20,t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
    t.w32(previous+16,successor)
    t.args(r3=owner,r4=node)
