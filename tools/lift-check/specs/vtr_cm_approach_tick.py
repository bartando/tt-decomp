"""cmApproachOperator::Tick (0x82278B90), slot 10: approach the result toward portA."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::cmApproachOperator::Tick"
ADDRESS = 0x82278B90
SOURCE = "src/rage/misc/rage_cm.cpp"

EXTERNS = {
    "rage::cmNode_GetFloat": 0x82179350,
    "rage::cmNode_GetVector": 0x821792D8,
    "cmApproach_VectorStep": 0x82277D38,
    "g_sysTimeManager": 0x825CAEB8,
    "rage::g_cm_frameTime": 0x825C4958,
    "rage::g_cm_zeroFloat": 0x8202D110,
}


def _float(ctx):
    return ctx.rng.choice([0.0, 0.5, 1.0, -2.0, ctx.rng.uniform(-10, 10)])


CALLS = {
    "rage::cmNode_GetFloat": stub(ret=_float),
    "rage::cmNode_GetVector": stub(out={"r3": 16}),
    "cmApproach_VectorStep": stub(ret="void", args=("r3", "r4", "f1", "f2"),
                                  deref={"r3": 16, "r4": 16}),
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x30, "node")
    res = t.alloc(0x20, "result", fill="zero")
    t.floats(res, 4, -10, 10)
    t.w8(res + 0x10, rng.choice([2, 4, 2, 4, 0, 1, 3]))
    t.w32(node + 0x28, res)
    t.wf32(0x825CAEB8 + 8, rng.uniform(0, 2))
    t.wf32(0x825C4958, rng.uniform(0, 0.1))
    t.args(r3=node)
