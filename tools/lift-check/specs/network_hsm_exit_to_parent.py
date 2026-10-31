"""0x823ED988: leave active states, unlink notifications, cache child links."""
from liftcheck.spec import *
from liftcheck.machine import STACK_LO, STACK_HI
FUNCTION='snSession_AssociateConnections'
ADDRESS=0x823ED988
SOURCE='src/rage/network/hsm_transition.cpp'
TRIALS=1000
def _log(c):
    assert STACK_LO<=c.r(3)<STACK_HI
    c.rec.strings[0]=b'<scratch>'
    text=bytearray()
    while True:
        byte=c.read(c.r(4)+len(text),1)
        text+=byte
        if byte==b'\0': break
    c.rec.derefs['format']=(bytes(text),None)
    c.ret()
CALLS={'snSession_D418_w':run(),
       'state.vfn_2':stub(ret=0x45000000),
       'state.vfn_8':stub(ret=0x45000040),
       'state.vfn_15':stub(ret='void',args=('r3',)),
       'snSession_DDB8_w':stub(ret='void',args=('r3','r4')),
       'nop_8240E6D0':model(_log,args=('r3','r5'),deref={'r3':0})}
def inputs(t):
    context=t.alloc(128,'context')
    names=t.map(0x45000000,4096,'name and notification')
    t.put(names,b'State\0')
    states=[t.alloc(24,'state') for _ in range(20)]
    table=t.vtable('state',16)
    for i,state in enumerate(states):
        t.w32(state,table)
        t.w32(state+8,t.rng.choice(states[:i]) if i else 0)
    left=t.rng.choice(states[1:])
    right=t.rng.choice(states[1:])
    active=t.rng.choice([left,states[0]])
    # root is an early-stop case only; leaving it has no parent to cache into.
    limit=t.rng.choice([0,1,2,0xFFFFFFFF,t.u32()])
    count=t.rng.choice([0,1,2,0xFFFFFFFF,t.u32()])
    if active==states[0]: limit,count=1,1
    t.w32(context+8,active)
    t.w32(context+0x58,limit)
    t.w32(context+0x54,count)
    t.args(r3=context,r4=t.rng.choice([0,left,left,left]),r5=right)
