"""0x820F1C00: grmModel draw, re-lifted from disasm/sections/.text.s.

r3=model, r4=shader group, r5=matrix palette, r6=matrix count, r7=shader
filter, r8=LOD. Compare slot-4 target and all seven arguments, matrix bytes,
all memory, and the real 0x820F0AA0 queue helper's bucket/link writes.

Cover empty and >255 counts; unsigned u16 shader indices; full-word filters;
forced shader bit 0 versus ordinary flags; adjacent draw keys (even when the
next shader fails the filter); forced last-run handling; and callback changes
to count, indices, shader array, forced shader and queue. No ignored memory.
Run with --trials 1000 --seed 1 and --seed 7. Mutation proof lives beside this
spec in _grm_model_draw_mutations.py. Call boundaries do not verify GPU output.
"""
from liftcheck.spec import *

FUNCTION = "rage::grmModel::Draw"
ADDRESS = 0x820F1C00
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000
QUEUE = 0x825EB1D0
FORCED = 0x82606350
EXTERNS = {"rage::g_iccProfilePtr": QUEUE, "rage::g_currentGeometry": FORCED}


def shader_draw(ctx):
    obj = ctx.r(4)
    control = obj + 0x20
    if ctx.read(control, 4) == bytes(4):
        return
    ctx.write(control, bytes(4))
    # The test sidecar describes a single callback mutation on both sides.
    ctx.write(obj + 0x16, ctx.read(control + 4, 2))
    ctx.write(obj + 0x0C, ctx.read(control + 8, 4))
    group = int.from_bytes(ctx.read(control + 12, 4), "big")
    ctx.write(group + 8, ctx.read(control + 16, 4))
    ctx.write(FORCED, ctx.read(control + 20, 4))
    ctx.write(QUEUE, ctx.read(control + 24, 4))


CALLS = {
    "rage::grmDrawQueue_AddGeometry": run(args=("r3", "r4", "r5", "r6")),
    "shader.vfn_4": model(shader_draw,
                          args=("r3", "r4", "r5", "r6", "r7", "r8", "r9"),
                          deref={"r6": 64}),
}


def inputs(t):
    r = t.rng
    n = r.choice([0, 1, 2, 3, 6, 12]) if t.index % 50 else 260
    capacity = max(n, 12)
    change = n > 0 and r.randrange(2) == 0
    filter_value = r.choice([0, 1, 2, 7, 31, 32, 255, 0xFFFFFFFF, t.u32()])
    # Force plenty of successful draws and callback mutations.
    if change:
        filter_value = r.choice([0, 1, 7, 31])
    vt = t.vtable("shader", slots=6)
    shaders = []
    keys = r.choice([[3] * 8, list(range(8)), [1, 1, 2, 2, 1, 1, 2, 2]])
    for k in range(8):
        sh = t.alloc(16, f"shader{k}")
        t.w32(sh, vt)
        kind = filter_value if k == 0 or r.randrange(2) else r.randrange(32)
        flags = (r.getrandbits(16) & ~0x3E0) | ((kind & 31) << 5)
        t.w16(sh + 4, flags)
        t.w16(sh + 6, keys[k])
        t.w32(sh + 8, 0)  # queue index zero means not yet registered
        shaders.append(sh)

    # Sparse high indices catch byte truncation and signed-halfword loads.
    indices = [0, 1, 2, 3, 4, 5, 6, 7]
    if t.index % 20 == 0:
        indices = [0, 1, 255, 256, 32767, 32768, 65534, 65535]
    arrays = []
    for variant in range(2):
        arr = t.alloc((max(indices) + 1) * 4, f"shaderArray{variant}")
        for k, index in enumerate(indices):
            t.w32(arr + index * 4, shaders[(k + variant) % 8])
        arrays.append(arr)
    group = t.alloc(16, "shaderGroup")
    t.w32(group + 8, arrays[0])
    buffers = []
    for variant in range(2):
        buf = t.alloc(capacity * 2, f"shaderIndices{variant}")
        for k in range(capacity):
            t.w16(buf + 2 * k, indices[0 if k == 0 else r.randrange(8)])
        buffers.append(buf)
    obj = t.alloc(0x40, "modelAndCallbackControl")
    t.w32(obj + 0x0C, buffers[0])
    t.w16(obj + 0x16, n)
    transforms = t.alloc(64, "transforms")
    t.floats(transforms, 16)

    buckets = t.alloc(8 * 10, "shaderBuckets")
    draws = t.alloc(8 * (capacity + 10), "drawEntries")
    queue = t.alloc(16, "queue")
    t.w32(queue, buckets)
    t.w16(queue + 4, 1)
    t.w32(queue + 8, draws)
    t.w16(queue + 12, 1)
    forced = r.choice([0, 0, shaders[0], shaders[-1]])
    if change:
        forced = 0
    t.w32(QUEUE, 0 if change or r.randrange(2) else queue)
    t.w32(FORCED, forced)
    t.w32(obj + 0x20, int(change))
    t.w16(obj + 0x24, r.choice([0, 1, capacity]))
    t.w32(obj + 0x28, buffers[r.randrange(2)])
    t.w32(obj + 0x2C, group)
    t.w32(obj + 0x30, arrays[r.randrange(2)])
    t.w32(obj + 0x34, r.choice([0, shaders[0], shaders[-1]]))
    t.w32(obj + 0x38, r.choice([0, queue]))
    t.args(r3=obj, r4=group, r5=transforms,
           r6=r.choice([0, 1, 255, 256, 511, 512, t.u32()]),
           r7=filter_value, r8=r.choice([0, 1, 3, t.u32()]))
