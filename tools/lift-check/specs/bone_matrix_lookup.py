"""0x821D0A30: mapped/direct IDs, full matrix copy, untouched failure output."""
from liftcheck.spec import *

FUNCTION = "game_0A30"
ADDRESS = 0x821D0A30
SOURCE = "src/anim/bone_matrix_lookup.cpp"
TRIALS = 1000

CALLS = {0x821D04F0: run(), 0x8240E6D0: stub(ret="void", args=("r3",))}


def inputs(t):
    rng = t.rng
    bone = t.alloc(0x44, "bone")
    state = t.alloc(0x18, "sampleState")
    boneMap = t.alloc(0x20, "boneMap")
    matrices = t.alloc(9 * 64, "sampleMatrices")
    output = t.alloc(64, "output")
    mapped = rng.choice([False, True])
    t.w32(boneMap + 0x14, rng.getrandbits(32) & ~2 | (2 if mapped else 0))
    entries = t.alloc(8 * 4, "mapEntries")
    count = rng.randrange(9)
    ids = rng.sample(range(0x10000), count)
    ids.sort()
    for i, boneId in enumerate(ids):
        t.w16(entries + i * 4, boneId)
        t.w16(entries + i * 4 + 2, rng.randrange(8))
    t.w16(boneMap + 0x1C, count)
    t.w32(boneMap + 0x18, entries)
    boneId = rng.choice(ids) if mapped and ids and rng.choice([False, True]) else rng.randrange(8)
    t.w16(bone + 0x40, boneId)
    t.w32(state + 4, boneMap)
    t.w32(state + 0x14, matrices)
    if t.index % 4 == 0:
        output = matrices + rng.randrange(4) * 16
    t.args(r3=bone, r4=output, r5=state)
