"""Cached selection, teardown, and entry initialization across distinct instances."""
from liftcheck.spec import *

FUNCTION = "grmShaderInstance_Select"
ADDRESS = 0x8215AE90
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000
EXTERNS = {
    "g_grmShaderInstance_previous": 0x825EBC44,
    "g_grmShaderInstance_activeEntry": 0x825EBC48,
    "g_grmShaderInstance_context": 0x82617E60,
}
CALLS = {
    "grmShaderInstance_Unbind": stub(ret="void", args=("r3",)),
    "rage_8C48": stub(ret="void", args=("r3", "r4")),
    "grmShaderInstance_FilterAndUploadParameters": stub(ret="void", args=("r3",)),
}


def inputs(t):
    rng = t.rng
    instance = t.alloc(704, "current instance")
    old = t.alloc(704, "old instance")
    entries = t.alloc(0x10000, "entry table")
    descriptor = t.alloc(16, "descriptor")
    index = rng.choice([0, 1, 0x3fff, rng.randrange(0x4000)])
    entry = (index << 18) | rng.randrange(1, 0x40000)
    mode = rng.randrange(8)
    if mode in (0, 6):
        entry = 0
    previous = [0, old, instance, instance, instance, old, old, instance][mode]
    cached_entry = entry if mode in (2, 3, 4) else entry ^ 1
    context_value = t.u32()
    bound_context = context_value if mode == 2 else context_value ^ 1
    bound_param = instance if mode in (2, 4) else old
    t.w32(0x82617E60, instance)
    t.w32(0x82617E70, context_value)
    t.w32(0x825EBC44, previous)
    t.w32(0x825EBC48, cached_entry)
    t.w32(0x825EBC50, bound_param)
    t.w32(0x825EBC54, bound_context)
    t.w32(instance + 512, entries)
    wrong_index = (entry >> 19) & 0x3fff
    if wrong_index != index:
        alternate = t.alloc(16, "alternate descriptor")
        t.w32(alternate + 12, t.u32())
        t.w32(entries + wrong_index * 4, alternate)
    t.w32(entries + index * 4, descriptor)
    t.w32(descriptor + 12, t.u32())
    t.args(r3=t.u32(), r4=entry)
