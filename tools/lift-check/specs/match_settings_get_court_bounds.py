"""0x821C9CD0: per-side court limits; preserve w and scalar store/load order."""
from liftcheck.spec import *

FUNCTION = "pongMatchSettings_GetCourtBounds"
ADDRESS = 0x821C9CD0
SOURCE = "src/game/player/pong_gameplay_queries.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def inputs(t):
    settings = t.alloc(0x180, "settings")
    court = t.alloc(32, "court")
    low = t.alloc(16, "lower")
    high = t.alloc(16, "upper")
    t.w32(0x8271A304, court)
    t.wf32(court + 24, t.f32(-50, 50))
    t.floats(settings + 128, 3, -50, 50)
    index = t.pick([0, 1, 2, 7, 31])
    t.w8(settings + 64 + index, t.pick([0, 1, 2, 128, 255]))
    # Alias both outputs and live source fields as well as ordinary buffers.
    mode = t.index % 8
    if mode == 1:
        high = low
    elif mode == 2:
        low = settings + 128
    elif mode == 3:
        high = settings + 128
    elif mode == 4:
        low = high + 4  # overlap only part of the output vectors
    t.args(r3=settings, r4=index, r5=low, r6=high)
