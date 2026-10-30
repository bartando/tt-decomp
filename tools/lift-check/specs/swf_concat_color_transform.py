"""Signed 2.6 color composition, wrapping offsets, truncating /255 tint.

All byte values are legal; out/local/parent can alias, including shifted
partial overlaps. Upper tint bits must be ignored. No stubs or ignored bytes.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfConcatColorTransform"
ADDRESS = 0x823FAE98
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000

EDGE = (0, 1, 63, 64, 65, 127, 128, 129, 192, 254, 255)


def inputs(t):
    r = t.rng
    arena = t.alloc(64, "colorTransforms")
    mode = t.index % 10
    out, local, parent = arena + 24, arena + 8, arena + 40
    if mode == 1:
        out = local
    elif mode == 2:
        out = parent
    elif mode == 3:
        local = parent
    elif mode == 4:
        out = local = parent
    elif mode == 5:
        out = local + r.choice((-7, -4, -1, 1, 4, 7))
    elif mode == 6:
        out = parent + r.choice((-7, -4, -1, 1, 4, 7))
    elif mode == 7:
        parent = local + r.choice((-7, -4, -1, 1, 4, 7))
        out = local + r.randrange(-7, 8)
    if t.index % 3 == 0:
        for p in (local, parent):
            for i in range(8):
                t.w8(p + i, r.choice(EDGE))
    rgb = r.getrandbits(32)
    alpha = r.getrandbits(32)
    if mode in (8, 9):
        # Independent channel tints: zero, full scale, fractions and negatives.
        rgb = r.choice((0, 0xFFFFFF, 0x123456, 0xFF0000, 0x00FF00, 0x0000FF, 0x7F80FE)) | (r.randrange(256) << 24)
        alpha = (alpha & 0xFFFFFF00) | r.choice(EDGE)
    t.args(r3=out, r4=local, r5=parent, r6=rgb, r7=alpha)
