"""Animation type checks use three image type tokens."""
from liftcheck.spec import *

FUNCTION = "pcrAnimEvent::MatchesType"
ADDRESS = 0x820DE7D8
SOURCE = "src/anim/pcr_anim_events.cpp"


def inputs(t):
    values = [t.u32() for _ in range(3)]
    for address, value in zip((0x825C9C60, 0x825C803C, 0x825C8038), values):
        t.w32(address, value)
    t.args(r3=t.alloc(0x28, "event"), r4=t.pick([*values, 0, t.u32()]))
