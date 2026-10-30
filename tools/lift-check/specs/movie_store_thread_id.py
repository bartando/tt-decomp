from liftcheck.spec import *

FUNCTION = "CCalMoviePlayer::SaveAndReplaceFiberContext"
ADDRESS = 0x8235EB30
SOURCE = "src/game/misc/pong_misc.cpp"
TRIALS = 1000
RET = None
CALLS = {"xe_GetCurrentThreadId": stub(ret=lambda c: c.rng.getrandbits(32))}


def inputs(t):
    obj = t.alloc(0x288c, "movie")
    t.w32(obj + 0x2888, t.rng.choice((0, 1, 0xffffffff, t.u32())))
    t.args(r3=obj)
