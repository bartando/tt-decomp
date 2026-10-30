"""Filter both dirty banks in VMX-sized groups, then upload the instance.

Counts include nonmultiples of four, and pointers cover every vector alignment.
The banks and their masks are disjoint, with valid storage for the rounded-up
last group. The upload is stubbed so filtering and call order can be compared.
"""
from liftcheck.spec import *

FUNCTION = "grmShaderInstance_FilterAndUploadParameters"
ADDRESS = 0x82159E70
SOURCE = "src/rage/rage_grm.cpp"
CALLS = {"rage_6370": stub(ret="void", args=("r3",), deref={"r3": 128})}


def inputs(t):
    rng = t.rng
    state = t.alloc(736, "instance", align=16) + rng.randrange(16)
    dirty = t.alloc(176, "secondDirty", align=16) + rng.randrange(16)
    mask = t.alloc(176, "secondMask", align=16) + rng.randrange(16)
    counts = [rng.choice([0, 1, 2, 3, 4, 5, 7, 8, 9, 12, 15, 16])
              for _ in range(2)]
    t.w32(state + 256, dirty)
    t.w32(state + 260, mask)
    t.w32(state + 288, counts[0])
    t.w32(state + 292, counts[1])
    t.args(r3=state)
