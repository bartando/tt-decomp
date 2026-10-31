from liftcheck.spec import *
CALLS = {'atSingleton_6F98_g': stub(args=()), 'msgSink_GetDeadlineOverrun': run(),
         'msgMsgSink::DispatchVirtualMethod': run(), 'target.vfn_9': stub(ret='void',args=('r3','r4'))}
def make_sink(t):
    sink=t.alloc(0x1C0,'sink')
    t.w32(sink+0x16C,t.rng.choice([0,0,1,1000,0xFFFFFFFF,t.u32()]))
    t.w32(sink+0x170,t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
    t.w32(sink+0x174,t.rng.choice([0,1,0x7FFFFFFF,0x80000000,0xFFFFFFFF,t.u32()]))
    return sink

def make_peer(t):
    peer=t.alloc(64,'peer')
    attached=t.alloc(32,'attached')
    owner=t.alloc(64,'owner')
    target=t.alloc(16,'target')
    t.w32(target,t.vtable('target',10))
    t.w32(owner+0x24,t.rng.choice([target,0]))
    t.w32(attached+0x18,owner)
    t.w32(peer+0x28,t.rng.choice([attached,0]))
    return peer
