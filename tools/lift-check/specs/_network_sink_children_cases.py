from liftcheck.spec import *
SOURCE='src/game/network/msg_sink_children.cpp'
TRIALS=600
CALLS={'msgMsgSink_8E60_sp':run(),'msgMsgSink_8E88_sp':run(),
       'msgChild_HasPendingTarget':run(),
       'target.vfn_11':stub(ret=lambda c:c.rng.choice([0,0,0,1,256,0xFFFFFFFF]),args=('r3',)),
       'target.vfn_21':stub(args=('r3','r4'))}
def make_inner(t):
    sink=t.alloc(40,'inner sink')
    target=t.alloc(16,'target')
    t.w32(target,t.vtable('target',22))
    t.w32(sink+0x24,t.rng.choice([0,target,target]))
    return sink
def make_child(t):
    child=t.alloc(32,'child')
    inner=make_inner(t)
    t.w32(child+0x18,t.rng.choice([0,inner,inner]))
    return child
