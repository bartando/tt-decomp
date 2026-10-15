"""datResource pointer fixup (0x82121B00): rebase a pointer field through the TLS resource context."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "datResource_PointerFixup"
ADDRESS = 0x82121B00
SOURCE = "src/rage/data/dat_resource_fixup.cpp"

PAGES = 8
CTX_WORD = 0x825F5AAC   # scratch image word the KeTlsGetValue model returns (patched per trial)


def _tls_get(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(CTX_WORD, 4), "big"))


CALLS = {
    "ke_KeTlsAlloc_623C": returns(7),
    "ke_KeTlsGetValue_621C": model(_tls_get),
}


def inputs(t):
    rng = t.rng
    t.w32(0x825F5AA8, rng.choice([0, 0, 5]))    # g_datResourceTlsSlot
    field_block = t.alloc(0x40, "fields")
    field = field_block + 4 * rng.randrange(16)
    rsc = t.alloc(8 + 4 * PAGES + 0x50, "rsc", fill="zero")
    page_size = rng.choice([0x100, 0x1000])
    image_base = rng.getrandbits(32) & ~0xFFF
    for k in range(PAGES):
        t.w32(rsc + 8 + 4 * k, rng.getrandbits(32))
    if rng.random() < 0.6:      # the field lies in the image being placed
        t.w32(rsc + 0x00, field_block)
        t.w32(rsc + 0x48, rng.choice([0x40, field - field_block, max(0, field - field_block - 4)]))
    else:
        t.w32(rsc + 0x00, field + rng.choice([4, 8]))
        t.w32(rsc + 0x48, 0x40)
    t.w32(rsc + 0x04, image_base)
    t.w32(rsc + 0x4C, page_size)
    t.w32(field, rng.choice([0, image_base + rng.randrange(PAGES * page_size)]))
    t.w32(CTX_WORD, rsc if rng.random() < 0.85 else 0)
    t.args(r3=field)
