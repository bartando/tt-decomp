from liftcheck.spec import *

FUNCTION = "rage::cmCachedOperator_GetFloat"
ADDRESS = 0x82272588
SOURCE = "src/rage/misc/rage_cm.cpp"
TRIALS = 1000
RET = None


def dispatch(ctx):
    ctx.write(ctx.r(3), ctx.read(ctx.r(4), 4))

CALLS = {0x82275380: model(dispatch, args=("r3", "r4", "r5"), deref={"r4": 8})}


def inputs(t):
    node = t.alloc(32, "node")
    value = t.alloc(4, "value")
    output = t.alloc(4, "output")
    t.w32(node + 8, (t.u32() & ~0x30) | t.rng.choice((0, 0x10, 0x20, 0x30)))
    t.w32(node + 28, value)
    t.args(r3=node, r4=output)
