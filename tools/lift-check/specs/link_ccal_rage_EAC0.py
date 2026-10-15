"""rage_EAC0 (0x8235EAC0)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage_EAC0"
ADDRESS = 0x8235EAC0
SOURCE = "src/game/misc/ccal_movie_player.cpp"


def inputs(t):
    t.args(r3=t.alloc(0x10, "obj"))
