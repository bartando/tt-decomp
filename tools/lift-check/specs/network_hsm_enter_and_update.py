"""0x823EDA90: cache the entry path, run enter hooks, update under saved limit."""
from specs.network_hsm_exit_to_parent import _log
from liftcheck.spec import *
FUNCTION='snSession_ProcessPendingConnections'
ADDRESS=0x823EDA90
SOURCE='src/rage/network/hsm_transition.cpp'
TRIALS=1000
def _update(c):
    # The hook observes the temporary limit and can change the pending count.
    context=0x45000000
    c.rec.derefs['context']=(c.read(context+0x54,8),None)
    c.write(context+0x54,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.ret()
CALLS={'state.vfn_2':stub(ret=0x45000100),
       'state.vfn_7':stub(ret=lambda c:c.rng.choice([0,1,1,2,0xFFFFFFFF])),
       'state.vfn_8':stub(ret=0x45000140),
       'state.vfn_13':model(_update,args=('r3',)),
       'state.vfn_14':stub(ret='void',args=('r3',)),
       'snSession_DD10_w':stub(ret='void',args=('r3','r4')),
       'nop_8240E6D0':model(_log,args=('r3','r5'),deref={'r3':0})}
def inputs(t):
    context=t.map(0x45000000,4096,'context and name')
    t.put(context+0x100,b'State\0')
    states=[t.alloc(24,'state') for _ in range(12)]
    table=t.vtable('state',16)
    for i,state in enumerate(states):
        t.w32(state,table)
        t.w32(state+8,states[i-1] if i else 0)
        t.w32(state+0xC,states[i+1] if i<len(states)-1 else 0)
    active=t.rng.randrange(4)
    target=t.rng.randrange(active+1,10)
    t.w32(context+8,states[active])
    t.w32(context+0x54,t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
    t.w32(context+0x58,t.u32())
    t.args(r3=context,r4=t.u32(),r5=states[target])
