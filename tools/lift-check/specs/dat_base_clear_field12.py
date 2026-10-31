"""Clear the complete count word and preserve every neighboring byte."""
FUNCTION = 'datBase_ClearField12'
ADDRESS = 0x824885C8
SOURCE = 'src/rage/core/rage_core_utils.cpp'
TRIALS = 900


def inputs(t):
    obj = t.alloc(64, 'object')
    t.w32(obj + 12, t.rng.choice([0, 1, 255, 0x80000000, 0xFFFFFFFF, t.u32()]))
    t.args(r3=obj)
