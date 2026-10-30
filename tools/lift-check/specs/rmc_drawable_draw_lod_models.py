"""0x8225D8A0: draw one LOD's models, with mask and transform-state caching.

The descriptive name comes from shared rmcDrawable/fragDrawable draw slots
5/6/7, which pass their embedded LOD group at +0x10. It is not an original
debug symbol. Drawing, viewport matrix setup and shader updates are call
boundaries: compare every argument and all 64 matrix bytes, not GPU output.

Cover empty/large lists, null entries, all four LODs, mask word boundaries,
unsigned byte indices, noncanonical flags, identity/indexed cache transitions,
both skinned dispatches and rigid shader updates even on identity/cache hits.
Draw callbacks can shrink/grow the list, replace its backing array and change
the viewport/update flag, exercising the original's reloads across calls.
No ignored memory and no float tolerance.

Mutation check: PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python
    tools/lift-check/specs/_rmc_drawable_draw_lod_models_mutations.py
"""
from liftcheck.spec import *

FUNCTION = "rage::rmcDrawable_DrawLodModels"
ADDRESS = 0x8225D8A0
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000

VIEWPORT = 0x825EBAA0
UPDATE = 0x8260633D


def draw(ctx):
    # All three draw signatures put shaderGroup in r4 or r5.
    group_reg = 5 if ctx.rec.target == 0x820F1D80 else 4
    group = ctx.r(group_reg)
    trigger = int.from_bytes(ctx.read(group + 4, 4), "big")
    if trigger != ctx.r(3):
        return
    list_addr = int.from_bytes(ctx.read(group, 4), "big")
    replacement = ctx.read(group + 8, 4)
    ctx.write(list_addr, replacement)
    ctx.write(list_addr + 4, ctx.read(group + 12, 2))
    ctx.write(VIEWPORT, ctx.read(group + 16, 4))
    ctx.write(UPDATE, ctx.read(group + 20, 1))
    ctx.write(group + 4, bytes(4))  # one mutation per side, per trial


CALLS = {
    0x821538C0: stub(ret="void", args=("r3", "r4", "r5"), deref={"r4": 64, "r5": 64}),
    0x8225D798: stub(ret="void", args=("r3", "r4", "r5"),
                     deref={"r3": 64, "r4": 64, "r5": 64}),
    0x820F19C8: model(draw, args=("r3", "r4", "r5", "r6")),
    0x820F1C00: model(draw, args=("r3", "r4", "r5", "r6", "r7", "r8"), deref={"r5": 64}),
    0x820F1D80: model(draw, args=("r3", "r4", "r5", "r6", "r7", "r8", "r9"), deref={"r6": 64}),
}


def inputs(t):
    rng = t.rng
    n = rng.choice([0, 1, 2, 5, 12, 20]) if rng.randrange(40) else 260
    capacity = max(n, 12)
    lod = rng.randrange(4)
    transforms = t.alloc(256 * 64, "transforms")
    t.floats(transforms, 256 * 16, -10, 10)
    group = t.alloc(24, "shaderGroup")
    context = t.alloc(16, "drawContext")
    skin = t.alloc(16, "skinContext")
    viewport = t.alloc(0x400, "viewport")
    alternate_viewport = t.alloc(0x400, "alternateViewport")
    t.w32(VIEWPORT, viewport)
    t.w8(UPDATE, rng.choice([0, 0, 1, 2, 0x80, 0xFF]))

    words = [rng.getrandbits(32) for _ in range(8)]
    mask_kind = rng.randrange(4)
    if mask_kind == 1:
        words = [0] * 8
    elif mask_kind == 2:
        words = [0xFFFFFFFF] * 8
    bits = t.alloc(32, "maskWords")
    for k, word in enumerate(words):
        t.w32(bits + 4 * k, word)
    mask = t.alloc(4, "mask")
    t.w32(mask, bits)

    # Deliberate repeated-index/identity/skin transitions mixed with random
    # records. Distinct +0x10 and +0x13 bytes catch argument mixups.
    indices = [rng.choice([0, 31, 32, 63, 64, 127, 128, 255]) for _ in range(3)]
    pattern = rng.randrange(4)
    models = []
    model_indices = []
    for i in range(capacity):
        obj = t.alloc(32, f"model{i}")
        index = indices[(i // 2) % 3] if pattern != 3 else rng.randrange(256)
        special = rng.choice([0, 0, 0, 1, 2, 0x80, 0xFF])
        identity = rng.choice([0, 0, 1, 2, 0x80, 0xFF])
        if pattern == 0:
            special, identity = 0, 0
        elif pattern == 1:
            special, identity = (2 if i % 4 < 2 else 0), (0x80 if i % 4 == 2 else 0)
        elif pattern == 2:
            special, identity = 0xFF, 0
        t.w8(obj + 0x10, rng.choice([0, 1, 2, 31, 128, 255]))
        t.w8(obj + 0x13, index)
        t.w8(obj + 0x15, special)
        t.w8(obj + 0x18, identity)
        models.append(obj if i == 0 or rng.randrange(6) else 0)
        model_indices.append(index)

    data = t.alloc(capacity * 4, "models")
    alternate = t.alloc(capacity * 4, "alternateModels")
    for i, obj in enumerate(models):
        t.w32(data + 4 * i, obj)
        t.w32(alternate + 4 * i, models[-1 - i])
    lists = []
    for k in range(4):
        entry = t.alloc(8, f"lodList{k}")
        t.w32(entry, data)
        t.w16(entry + 4, n if k == lod else rng.randrange(capacity + 1))
        lists.append(entry)
    obj = t.alloc(0x40, "lodGroup")
    for k, entry in enumerate(lists):
        t.w32(obj + 0x30 + 4 * k, entry)

    # Force the first model through the optional filter when testing a callback.
    change = n != 0 and rng.randrange(3) == 0
    if change:
        index = model_indices[0]
        t.w32(bits + 4 * (index >> 5), words[index >> 5] | (1 << (index & 31)))
    t.w32(group, lists[lod])
    t.w32(group + 4, models[0] if change else 0)
    t.w32(group + 8, alternate if rng.randrange(2) else data)
    t.w16(group + 12, rng.choice([0, 1, capacity]))
    t.w32(group + 16, alternate_viewport)
    t.w8(group + 20, rng.choice([0, 1, 2, 0x80]))
    # The assembly spills only the low byte of r9; high bits must be irrelevant.
    skinned = (rng.getrandbits(24) << 8) | rng.choice([0, 1, 2, 0x80, 0xFF])
    t.args(r3=obj, r4=group, r5=transforms, r6=context, r7=lod,
           r8=0 if mask_kind == 0 else mask, r9=skinned, r10=skin)
