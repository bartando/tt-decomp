"""Insert/unlink through the image callback-list head under its shared critical section."""
from liftcheck.spec import *

FUNCTION = "_crt_critsec_init"
ADDRESS = 0x8242C178
SOURCE = "src/crt/startup.c"
CALLS = {
    "RtlEnterCriticalSection": stub(ret="void", args=("r3",)),
    "RtlLeaveCriticalSection": stub(ret="void", args=("r3",)),
}


def inputs(t):
    head = 0x825B0A4C
    a = t.alloc(12, "first")
    b = t.alloc(12, "second")
    for node, nxt, prev in ((head, a, b), (a, b, head), (b, head, a)):
        t.w32(node, nxt)
        t.w32(node + 4, prev)
    insert = t.rng.randrange(2)
    entry = t.alloc(12, "newEntry") if insert else t.pick([a, b])
    t.args(r3=entry, r4=insert)
