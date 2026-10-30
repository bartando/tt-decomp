"""Integer port evaluation: direct values, slot-5 out-param and invalid types.

Full-width signed results (not a bool/byte or the callback's r3). Null payload
for disconnected ports catches eager reads; all inputs and guards compare.
The synthetic callback writes an independently randomized value and returns a
separate decoy. Fully initialized, readable ports; no unwritten out-param case.
"""
from liftcheck.spec import *

FUNCTION = "rage::cmNode_GetDim"
ADDRESS = 0x82184B60
SOURCE = "src/rage/misc/rage_cm.cpp"
TRIALS = 1000


def get_dim(ctx):
    ctx.write(ctx.r(4), ctx.read(ctx.r(3) + 4, 4))
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 8, 4), "big"))


CALLS = {"node.vfn_5": model(get_dim, args=("r3", "r4"))}


def inputs(t):
    r = t.rng
    port = t.alloc(16, "portAndGuards") + 4
    kind = r.choice([0, 1, 1, 2, 2, 3, 5, 0xFFFFFFFF, 0x80000000, t.u32()])
    payload = 0
    if kind in (1, 2):
        payload = t.alloc(16, "payload")
        value = r.choice([0, 1, 255, 256, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, t.u32()])
        if kind == 2:
            t.w32(payload, t.vtable("node"))
            t.w32(payload + 4, value)
            t.w32(payload + 8, value ^ 0xA5A5A5A5)
        else:
            t.w32(payload, value)
    t.w32(port, payload)
    t.w32(port + 4, kind)
    t.args(r3=port)
