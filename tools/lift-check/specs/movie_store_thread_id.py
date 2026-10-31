from liftcheck.spec import *

FUNCTION = "_CCalMoviePlayer_EB30"
ADDRESS = 0x8235EB30
SOURCE = "src/game/misc/movie_worker_helpers.cpp"
TRIALS = 1000
CALLS = {"xe_GetCurrentThreadId": stub(ret=lambda c: c.rng.getrandbits(32), args=())}


def inputs(t):
    obj = t.alloc(0x288c, "movie")
    t.w32(obj + 0x2888, t.rng.choice((0, 1, 0xffffffff, t.u32())))
    t.args(r3=obj)
