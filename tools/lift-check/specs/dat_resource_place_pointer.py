"""Relocate an animation pointer slot and dispatch its resource placer."""
from liftcheck.spec import model, returns

FUNCTION = "datResource_PlacePointer"
ADDRESS = 0x8224DFC0
SOURCE = "src/rage/data/dat_resource_fixup.cpp"
TRIALS = 1000
CTX_WORD = 0x825F5AAC


def tls_get(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(CTX_WORD, 4), "big"))


CALLS = {
    0x8258623C: returns(7),
    0x8258621C: model(tls_get, args=("r3",)),
    "placed.vfn_1": model(lambda ctx: ctx.write(ctx.r(3) + 4, b"\x12\x34\x56\x78"),
                          args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    t.w32(0x825F5AA8, rng.choice([0, 5]))
    block = t.alloc(0x40, "slots")
    field = block + 16
    rsc = t.alloc(0x50, "resource", fill="zero")
    obj = t.alloc(16, "object")
    t.w32(obj, t.vtable("placed", 2))
    page_size = rng.choice([0x100, 0x1000, 0x10000])
    image_base = rng.choice([0x10000000, 0x70000000, 0xffff0000])
    page = rng.randrange(8)
    saved = (image_base + page * page_size + rng.randrange(1, page_size)) & 0xffffffff
    t.w32(rsc + 4, image_base)
    for i in range(8):
        t.w32(rsc + 8 + i * 4, (obj - saved if i == page else rng.getrandbits(32)) & 0xffffffff)
    t.w32(rsc + 0x4c, page_size)
    case = rng.randrange(7)
    base, size = [(field, 0), (field - 16, 16), (field - 16, 32),
                  (field + 4, 32), (field - 16, 12), (field - 16, 32),
                  (field - 16, 32)][case]
    t.w32(rsc, base)
    t.w32(rsc + 0x48, size)
    t.w32(field, 0 if case == 5 else saved)
    t.w32(CTX_WORD, 0 if case == 6 else rsc)
    t.args(r3=field)
