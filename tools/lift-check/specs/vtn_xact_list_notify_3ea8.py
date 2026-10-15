"""msgMsgSink_3EA8_g (0x82453EA8): walk the circular list whose sentinel is
+0x24 (head at +0x28, next at node+4) and hand each node r4, a pointer
(the caller passes this+0x148), via game_9D10_h."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "msgMsgSink_3EA8_g"
ADDRESS = 0x82453EA8
SOURCE = "src/game/network/msg_msg_sink.cpp"
RET = None

CALLS = {"game_9D10_h": stub(ret="void", args=("r3", "r4"), deref={"r4": 0})}


def inputs(t):
    obj = t.alloc(0x40, "list")
    sentinel = obj + 0x24
    prev = sentinel
    nodes = [t.alloc(0x10, f"node{i}") for i in range(t.rng.randrange(4))]
    head = nodes[0] if nodes else sentinel
    for i, n in enumerate(nodes):
        t.w32(n + 4, nodes[i + 1] if i + 1 < len(nodes) else sentinel)
    t.w32(obj + 0x28, head)
    t.args(r3=obj, r4=t.alloc(8, "arg"))
