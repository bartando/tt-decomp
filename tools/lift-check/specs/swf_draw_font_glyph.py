"""Font-atlas glyph rendering, texture cache, quad data and stream completion.

Valid, aligned, non-overlapping atlas/glyph/page/device storage only. Exercise
absent textures, optional byte page maps, cache hits/misses, nonzero glyphs,
arbitrary affine transforms, negative/zero scales, UVs and packed colours,
count-only with/without a cursor, and wrapping vertex counts. Guard bytes surround
the four 36-byte vertices. No ignored memory or float tolerance.

Texture binding and primitive begin are boundary models: bind observes the cache
write and can change the transform; begin changes stream state, so reads before
these calls are observable. This checks CPU output and call contracts, not GPU
pixels or a live match. Float exceptional values use the checker's usual NaN and
signed-zero rules. Invalid indices, pointer faults and state aliasing are outside
the supported inputs.
"""
from liftcheck.spec import *

FUNCTION = "liftcheck_glyph_adapter"
ADDRESS = 0x82403970
SOURCE = "tools/lift-check/specs/swf_draw_font_glyph_adapter.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
RET = None

STATE = 0x82606120
DEVICE = 0x825EB988
CURSOR, COUNT_ONLY, COUNT = 0x825EBA74, 0x825EBA84, 0x825EBA88
COLOR = 0x825CA604


def u32(c, addr):
    return int.from_bytes(c.read(addr, 4), "big")


def bind(c):
    texture = c.r(3)
    assert u32(c, STATE + 24) == texture, "texture cache must be written before binding"
    # Make a missing bind visible in memory as well as the call trace.
    c.write(texture + 4, c.read(STATE + 24, 4))
    if u32(c, texture + 32):
        c.write(STATE, c.read(texture + 8, 24))


def begin(c):
    assert (c.r(3), c.r(4)) == (4, 4)
    device = u32(c, DEVICE)
    config = device + 0x3560
    for i, address in enumerate((CURSOR, COUNT_ONLY, COUNT, COLOR)):
        c.write(address, c.read(config + 4 * i, 4))
    for i, address in enumerate((0x825EBA6C, 0x825EBA80, 0x825EBA8C,
                                 0x82602824, 0x8260283C)):
        c.write(address, c.read(config + 16 + 4 * i, 4))
    c.ret(r3=0)


CALLS = {
    "bindFontTexture": model(bind, args=("r3",)),
    0x82152A78: model(begin, args=("r3", "r4")),
}

SPECIAL = (0, 0x80000000, 1, 0x80000001, 0x7F7FFFFF, 0xFF7FFFFF,
           0x7F800000, 0xFF800000, 0x7FC00000)


def inputs(t):
    r = t.rng
    atlas = t.alloc(16, "fontAtlas")
    # Several pages and an 8-bit map catch wrong page width and indexing.
    textures = t.alloc(256 * 4, "texturePages")
    pages = t.alloc(32, "glyphPages") if r.randrange(2) else 0
    glyphs = t.alloc(32 * 32, "glyphs")
    index = r.choice((0, 1, 7, 15, 31, r.randrange(32)))
    page = r.choice((0, 1, 127, 128, 255)) if pages else 0
    texture = t.alloc(36, "selectedTexture")
    other_texture = t.alloc(36, "otherTexture")
    t.floats(other_texture + 8, 6, -10, 10)
    t.w32(other_texture + 32, 0)
    for slot in range(256):
        t.w32(textures + 4 * slot, other_texture)
    t.w32(textures + 4 * page, texture)
    if pages:
        t.w8(pages + index, page)
    t.w32(atlas, textures if r.randrange(8) else 0)
    t.w32(atlas + 4, glyphs)
    t.w32(atlas + 12, pages)
    t.floats(glyphs, 32 * 8, -1000, 1000)
    t.floats(STATE, 6, -10, 10)
    t.floats(texture + 8, 6, -10, 10)
    t.w32(texture + 32, r.randrange(2))
    t.w32(STATE + 24, r.choice((texture, texture, 0, textures)))
    t.w32(0x82602820, t.fake_fn("bindFontTexture"))

    vertices = t.alloc(16 + 4 * 36 + 16, "guardedVertices",
                       floats=[(16 + 36 * i, 6) for i in range(4)] +
                              [(16 + 36 * i + 28, 2) for i in range(4)])
    device = t.alloc(0x35A0, "graphicsDevice")
    t.w32(DEVICE, device)
    # These deliberately differ; omitting device completion must be visible.
    t.w32(device, 0xDEADBEEF)
    t.w32(device + 13652, r.getrandbits(32) & 0x7FFFFFFF)
    count_only = r.choice((0, 0, 1, 2, 0xFFFFFFFF))
    cursor = 0 if count_only and r.randrange(2) else vertices + 16
    for offset, value in enumerate((cursor, count_only,
                                    r.choice((0, 1, 0xFFFFFFFC, 0xFFFFFFFF, r.getrandbits(32))),
                                    r.getrandbits(32))):
        t.w32(device + 0x3560 + offset * 4, value)
    t.floats(device + 0x3570, 5, -10, 10)
    # Initial state must survive the no-textures return, but must be replaced by
    # begin on actual draws. A preexisting nonzero cursor is valid in both cases.
    t.w32(CURSOR, vertices + 16)
    t.w32(COUNT_ONLY, r.getrandbits(32))
    t.w32(COUNT, r.getrandbits(32))
    t.w32(COLOR, r.getrandbits(32))
    for address in (0x825EBA6C, 0x825EBA80, 0x825EBA8C, 0x825EBA78,
                    0x825EBA70, 0x82602824, 0x8260283C, 0x8202D110):
        t.wf32(address, r.uniform(-10, 10))
    t.wf32(0x820290EC, r.choice((1 / 1024, 1 / 256, -0.125, 0.0)))
    if r.randrange(5) == 0:
        # Patch one exceptional value among finite ones to expose fusion and
        # overflow/underflow behavior without making every vertex just NaN.
        address = r.choice((glyphs + index * 32 + r.randrange(8) * 4,
                            STATE + r.randrange(6) * 4,
                            texture + 8 + r.randrange(6) * 4))
        t.w32(address, r.choice(SPECIAL))
    t.args(r3=atlas, f1=r.uniform(-1000, 1000), f2=r.uniform(-1000, 1000),
           f3=r.choice((0.0, -0.0, 1.0, -1.0, r.uniform(-10, 10))), r7=index)
