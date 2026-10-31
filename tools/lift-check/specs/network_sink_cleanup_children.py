"""0x82454550: pending children still get serviced after state reaches six."""
from specs._network_sink_children_cases import *
FUNCTION='msgMsgSink_4550_g'
ADDRESS=0x82454550
CALLS={**CALLS,'msgSink_HasPendingChildren':run(),
       'sink.vfn_1':stub(ret='void',args=('r3','r4')),
       'game_A650_h':stub(ret='void',args=('r3',))}
def inputs(t):
    sink=t.alloc(96,'sink')
    t.w32(sink,t.vtable('sink',2))
    t.w32(sink+0x50,t.rng.choice([0,3,4,6,6,6,0xFFFFFFFF,t.u32()]))
    head=sink+0x24
    previous=head
    for i in range(t.rng.randrange(7)):
        child=make_child(t)
        t.w32(previous+4,child)
        previous=child
    t.w32(previous+4,head)
    t.args(r3=sink)
