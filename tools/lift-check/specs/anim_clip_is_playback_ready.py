"""0x820D6AA0: ordered float gates, byte gates and independent clip flags."""
from liftcheck.spec import *

FUNCTION = "pongAnimClip_IsPlaybackReady"
ADDRESS = 0x820D6AA0
SOURCE = "src/game/player/pong_gameplay_queries.cpp"
TRIALS = 1000


def inputs(t):
    clip = t.alloc(0x150, "clip")
    # First 256 cases vary every flag bit with all other gates open.
    flags = t.index % 256
    progress, position, active, stopped = 1.0, 0.0, 255, 0
    if t.index >= 256:
        flags = t.pick([1, 1, 5, 9, 13, t.u32() & 255])
        progress = t.pick([1.0, 0.0, -0.0, -1.0, 1e-40, float('nan'), float('inf')])
        position = t.pick([0.0, -0.0, -1e-40, -1.0, 1.0, float('nan'), float('inf')])
        active = t.pick([0, 1, 2, 128, 255])
        stopped = t.pick([0, 0, 1, 2, 128, 255])
    # Isolate each scalar gate with the remaining conditions satisfied.
    if 256 <= t.index < 282:
        flags, active, stopped = 1, 255, 0
        values = [0.0, -0.0, -1e-40, 1e-40, -1.0, 1.0, float("nan"), float("inf"), -float("inf")]
        progress, position = 1.0, 0.0
        if t.index < 265:
            progress = values[t.index - 256]
        elif t.index < 274:
            position = values[t.index - 265]
        else:
            active, stopped = [(0, 0), (1, 0), (2, 0), (255, 0), (1, 1), (1, 2), (1, 128), (1, 255)][t.index - 274]
    t.wf32(clip + 128, progress)
    t.wf32(clip + 288, position)
    t.w8(clip + 312, flags)
    t.w8(clip + 138, active)
    t.w8(clip + 136, stopped)
    t.args(r3=clip)
