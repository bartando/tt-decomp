from liftcheck.spec import *

FUNCTION = "util_B188"
ADDRESS = 0x823FB188
SOURCE = "src/rage/core/rage_core_utils.cpp"
TRIALS = 1000
EXTERNS = {"g_network_array1": 0x82619AF0}

def inputs(t):
    context = t.alloc(1100, "context")
    entries = t.alloc(128, "entries")
    index = t.rng.randrange(16)
    table = t.rng.randrange(4)
    entry = t.rng.choice([0xffffffff, 0, 1, 7, 31])
    t.w32(context + index * 8, table)
    t.w32(context + index * 8 + 4, entry)
    t.w32(context + (table + 261) * 4, entries)
    for i in range(4):
        t.w8(EXTERNS["g_network_array1"] + i * 36 + 28, t.rng.choice([0, 1, 2, 255]))
    t.args(r3=context, r4=index)
