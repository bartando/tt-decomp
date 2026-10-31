"""0x82282E70: horizontal flight basis, side orientation, preserved vertical spin."""
from liftcheck.spec import *

FUNCTION = "phBoundCapsule_2E70_fw"
ADDRESS = 0x82282E70
SOURCE = "src/game/player/player_spin_helpers.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
EXTERNS = {"g_pTableDims": 0x8271A304}
CALLS = {0x8227DD20: stub(ret=0.0, args=("f1",))}


def inputs(t):
    hit = t.alloc(0x80, "hit", floats=[(0x20, 4), (0x60, 4)])
    t.floats(hit + 0x20, 4, -8, 8)
    t.floats(hit + 0x60, 4, -8, 8)
    # Vary side, axial/diagonal and zero horizontal flight independently.
    mode = t.index % 10
    t.wf32(hit + 0x68, [-3, 0, 3][t.index % 3])
    if mode == 0:
        t.wf32(hit + 0x20, 0)
        t.wf32(hit + 0x60, 0)
    elif mode == 1:
        t.wf32(hit + 0x20, 2)
        t.wf32(hit + 0x60, 2)
        t.wf32(hit + 0x28, 3)
        t.wf32(hit + 0x68, 3)
    elif mode == 2:
        t.wf32(hit + 0x20, 1.0e-40)
        t.wf32(hit + 0x60, -1.0e-40)
    elif mode == 3:
        t.wf32(hit + 0x20, -1.0e-40)
        t.wf32(hit + 0x60, 1.0e-40)
        t.wf32(hit + 0x28, -1.0e-40)
        t.wf32(hit + 0x68, 1.0e-40)
    spin = hit + 0x20 if t.index % 17 == 0 else hit + 0x60 if t.index % 17 == 1 else t.alloc(16, "spin", floats=[(0, 4)])
    t.floats(spin, 4, -10, 10)
    dims = t.alloc(0x20, "tableDims", floats=[(0x14, 2)])
    t.wf32(dims + 0x14, t.rng.uniform(0.5, 1.5))
    t.wf32(dims + 0x18, t.rng.choice([0, 2.7439, t.rng.uniform(1, 4)]))
    t.w32(t.sym("g_pTableDims"), dims)
    t.args(r3=hit, r4=spin)
