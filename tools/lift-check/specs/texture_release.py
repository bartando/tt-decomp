"""16-bit wrapping reference count, deleting virtual, and returned count."""
from liftcheck.spec import *

FUNCTION = "rage::Release"
ADDRESS = 0x820C2E18
SOURCE = "src/graphics/texture_reference.cpp"
TRIALS = 600


def destroy(c):
    c.write(c.r(3) + 6, b"\xa5\x5a")
    c.ret(r3=0x12345678)


CALLS = {"texture.vfn_0": model(destroy, args=("r3", "r4"))}


def inputs(t):
    texture = t.alloc(32, "texture")
    t.w32(texture, t.vtable("texture", 26))
    t.w16(texture + 6, t.rng.choice((0, 1, 1, 2, 0x7fff, 0xffff, t.rng.randrange(65536))))
    t.args(r3=texture)
