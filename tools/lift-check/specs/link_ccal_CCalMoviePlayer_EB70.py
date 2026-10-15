"""CCalMoviePlayer_EB70 (0x8235EB70)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "CCalMoviePlayer_EB70"
ADDRESS = 0x8235EB70
SOURCE = "src/game/misc/ccal_movie_player.cpp"


def inputs(t):
    t.args(r3=t.alloc(0x2890, "obj"))
