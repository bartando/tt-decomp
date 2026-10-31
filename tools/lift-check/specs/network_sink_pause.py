"""0x82453C88: cache pause time, rebase pending deadlines, walk child sinks."""
from liftcheck.spec import *
FUNCTION = "msgMsgSink_3C88_g"
ADDRESS = 0x82453C88
SOURCE = "src/game/network/pong_network_io.cpp"
TRIALS = 600
CALLS = {"atSingleton_6F98_g": stub(args=()), "msgChild_SetPaused": stub(args=('r3', 'r4'))}
def inputs(t):
    sink = t.alloc(0x80, 'sink')
    t.w32(sink + 0x50, t.rng.choice([-1, 0, 3, 4, 5, 6]))
    t.w8(sink + 0x34, t.rng.randrange(256))
    for offset in [0x24, 0x38]:
        head = sink + offset
        previous = head
        for i in range(t.rng.randrange(5)):
            node = t.alloc(0x20, f'node_{offset}_{i}')
            t.w32(previous + 4, node)
            previous = node
        t.w32(previous + 4, head)
    t.args(r3=sink, r4=t.rng.choice([0, 1, 2, 0x100, 0xFFFFFFFF]))
