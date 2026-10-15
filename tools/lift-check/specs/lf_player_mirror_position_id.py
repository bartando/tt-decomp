"""pongPlayer_0270_g (0x821E0270): mirrors a ring position id (0x22..0x31) by four flag bytes."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongPlayer_0270_g"
ADDRESS = 0x821E0270
SOURCE = "src/game/player/pong_player.cpp"
EXTRA_RANGES = [(0x821E02B0, 0x821E02D0), (0x821E032C, 0x821E0348),
                (0x821E03D0, 0x821E03F0), (0x821E044C, 0x821E0468)]


def inputs(t):
    obj = t.alloc(8, "flags")
    for i in range(4, 8):
        t.w8(obj + i, t.rng.choice([0, 0, 1, 0x80]))
    t.args(r3=obj, r4=t.rng.choice(list(range(0x20, 0x34)) + [0, -1, 0x7FFFFFFF]))
