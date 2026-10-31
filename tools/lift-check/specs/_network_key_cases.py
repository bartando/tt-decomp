from liftcheck.spec import *
SOURCE='src/game/network/msg_sink_key.cpp'
TRIALS=600
CALLS={'msgSink_MatchesKey':run(),'atSingleton_9B98_p39':run(),
       'msgMsgSink_3D70_p39':run(),
       'target.vfn_13':stub(ret=lambda c:c.rng.choice([0,0x45000000,0x45000040,0x45000080]),args=('r3','r4'))}
def key(t):
    t.map(0x45000000,4096,'keys')
    return t.rng.choice([0,0x45000000,0x45000040,0x45000080])
def inner(t):
    sink=t.alloc(40,'inner')
    target=t.alloc(16,'target')
    t.w32(target,t.vtable('target',14))
    t.w32(sink+0x24,t.rng.choice([0,target,target]))
    return sink
def child(t):
    node=t.alloc(32,'child')
    first=inner(t)
    second=inner(t)
    t.w32(node+0x18,t.rng.choice([0,first,first]))
    t.w32(node+0x1C,t.rng.choice([0,second,second]))
    return node
def children(t):
    sink=t.alloc(56,'children owner')
    head=sink+0x24
    previous=head
    for i in range(t.rng.randrange(6)):
        node=child(t)
        t.w32(previous+4,node)
        previous=node
    t.w32(previous+4,head)
    return sink
