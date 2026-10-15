"""pongPlayer_SelectShotType (0x82199A70): 5, 9 (posting 0x101A) or 3."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongPlayer_SelectShotType"
ADDRESS = 0x82199A70
SOURCE = "src/game/player/pong_player.cpp"

CALLS = {0x8225E6E0: stub(ret="void")}   # PostGameMessage(id, flags, 0, 0)


def inputs(t):
    rng = t.rng
    flags = t.alloc(0x08, "flags", fill="zero")
    t.w8(flags + 4, rng.choice([0, 1, 0x80]))
    t.w8(flags + 6, rng.choice([0, 1, 0x80]))
    t.args(r3=flags, r4=rng.choice([0, 1, 2, 7]))
