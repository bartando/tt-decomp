from specs._network_key_cases import *
FUNCTION='msgMsgSink::GetNestedObjectValue'
ADDRESS=0x8244E148
def inputs(t):
    sink=t.alloc(64,'sink')
    owner=children(t)
    t.w32(sink+0x34,t.rng.choice([0,owner,owner]))
    t.args(r3=sink,r4=key(t))
