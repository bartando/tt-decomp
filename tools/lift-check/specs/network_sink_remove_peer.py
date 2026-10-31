from specs._network_sink_deadline_cases import *
FUNCTION = 'msgMsgSink::vfn_65'
ADDRESS = 0x82456810
SOURCE = 'src/game/network/msg_sink_timing.cpp'
TRIALS = 800
def inputs(t):
    sink=make_sink(t)
    peer=t.alloc(32,'peer info')
    t.w32(sink+0x198,peer)
    t.w16(peer+0x18,t.rng.randrange(65536))
    t.w32(sink+0x19C,t.rng.choice([0,1,1,1,2]))
    t.w32(sink+0x17C,t.rng.choice([0,0,0,1]))
    keys=[t.alloc(16,'key') for _ in range(5)] + [0]
    for offset in [0x34,0x18C,0x188,0x190]: t.w32(sink+offset,t.rng.choice(keys))
    t.args(r3=sink,r4=t.rng.choice(keys))
