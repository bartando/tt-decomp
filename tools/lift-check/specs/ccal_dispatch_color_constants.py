"""CCalMoviePlayer_CF28_wrh: the original unpacks the colour with vupkd3d128, which
lift-check doesn't emulate, so this spec reports "unsupported" (the self-test
relies on that)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "CCalMoviePlayer_CF28_wrh"
ADDRESS = 0x8235CF28
SOURCE = "src/game/misc/pong_misc.cpp"


def inputs(t):
    device = t.alloc(0x100, "device")
    t.args(r3=device, f1=t.f32(0, 1), r4=t.rng.randrange(4), r5=t.pick([0, 0x100]),
           r6=t.u32(), r7=t.u32(), r8=t.u32(), r9=t.u32())
