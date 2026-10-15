"""fragDrawable::ProcessGeometry (0x820F1C00): per-index shader filter + slot-4 draw."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::fragDrawable::ProcessGeometry"
ADDRESS = 0x820F1C00
SOURCE = "src/rage/rage_grm.cpp"

OVERRIDE = 0x825EB1D0
FORCED = 0x82606350

CALLS = {
    # 0x820F0AA0 never writes r3, and the original keeps the override pointer
    # in r3 across the call instead of reloading it.
    "fragDrawable_0AA0_2h": stub(ret=lambda ctx: ctx.r(3), args=("r3", "r4", "r5", "r6", "r7")),
    "shader.vfn_4": stub(ret="void", args=("r3", "r4", "r5", "r6", "r7", "r8", "r9")),
}


def inputs(t):
    rng = t.rng
    n = rng.randrange(0, 7)
    nshaders = 4
    vt = t.vtable("shader")
    shaders = []
    for k in range(nshaders):
        sh = t.alloc(0x10, f"shader{k}")
        t.w32(sh, vt)
        t.w16(sh + 4, rng.choice([0, 1, 0x20, 0x21, 0x40, rng.getrandbits(16)]))
        t.w16(sh + 6, rng.randrange(0, 2))
        shaders.append(sh)
    arr = t.alloc(4 * nshaders, "shaderArray")
    for k, sh in enumerate(shaders):
        t.w32(arr + 4 * k, sh)
    container = t.alloc(0x10, "container")
    t.w32(container + 8, arr)
    idx = t.alloc(2 * max(n, 1), "indices")
    for k in range(n):
        t.w16(idx + 2 * k, rng.randrange(0, nshaders))
    obj = t.alloc(0x20, "model")
    t.w32(obj + 0x0C, idx)
    t.w16(obj + 0x16, n)
    t.w32(OVERRIDE, t.alloc(0x10, "override") if rng.random() < 0.25 else 0)
    t.w32(FORCED, shaders[rng.randrange(nshaders)] if rng.random() < 0.3 else 0)
    t.args(r3=obj, r4=container, r5=rng.getrandbits(32), r6=rng.getrandbits(32),
           r7=rng.choice([0, 1, 2, rng.randrange(32)]), r8=rng.getrandbits(32))
