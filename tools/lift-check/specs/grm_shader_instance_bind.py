"""Instance binding, including previous-instance teardown and aligned dirty clears."""
from liftcheck.spec import *

FUNCTION = "grmShaderInstance_Bind"
ADDRESS = 0x8215AF90
SOURCE = "src/rage/rage_grm.cpp"
EXTERNS = {"g_grmShaderInstance_previous": 0x825EBC44}
CALLS = {"grmShaderInstance_Unbind": stub(ret="void", args=("r3",))}


def inputs(t):
    rng = t.rng
    # Vary the instance's offset within a cache line; both clears align down.
    block = t.alloc(1024, "instance storage", align=128)
    instance = block + rng.randrange(8) * 16
    slot = t.alloc(4, "effect slot")
    table = t.alloc(0x10000, "entry table")
    entry = t.alloc(8, "entry")
    index = rng.choice([0, 1, 0x3fff, rng.randrange(0x4000)])
    entry_id = (index << 18) | rng.getrandbits(18)
    t.w32(slot, instance)
    t.w32(instance + 512, table)
    t.w32(table + index * 4, entry)
    t.w32(entry + 4, t.u32())
    previous = 0
    if rng.randrange(2):
        previous = instance if rng.randrange(4) == 0 else t.alloc(704, "previous instance")
    t.w32(0x825EBC44, previous)
    t.w32(0x825EBC4C, t.u32())
    flags = rng.choice([0, 1, 0x100, 0xff, 0x10001, t.u32()])
    t.args(r3=slot, r4=entry_id, r5=flags)
