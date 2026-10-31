"""0x82453F68: sentinel traversal and short-circuit on any nonzero response."""
from specs._network_sink_children_cases import *
FUNCTION='msgSink_HasPendingChildren'
ADDRESS=0x82453F68
def inputs(t):
    sink=t.alloc(56,'sink')
    head=sink+0x24
    previous=head
    for i in range(t.rng.randrange(7)):
        child=make_child(t)
        t.w32(previous+4,child)
        previous=child
    t.w32(previous+4,head)
    t.args(r3=sink)
