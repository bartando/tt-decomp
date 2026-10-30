"""Read all three supported-type slots from the image, including nonzero IDs."""
from liftcheck.spec import *

FUNCTION = "assetVersionsCharSpecific::IsSupported"
ADDRESS = 0x822283C8
SOURCE = "src/game/misc/pong_misc.cpp"


def inputs(t):
    values = [t.u32() for _ in range(3)]
    for address, value in zip((0x825C586C, 0x825C803C, 0x825C8038), values):
        t.w32(address, value)
    candidate = t.pick([*values, 0, t.u32()])
    t.args(r3=t.alloc(0x70, "versions"), r4=candidate)
