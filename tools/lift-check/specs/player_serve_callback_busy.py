"""0x820DD388: query the callback only when its kind field is nonzero."""
from liftcheck.spec import *

FUNCTION = "game_D388"
ADDRESS = 0x820DD388
SOURCE = "src/game/player/player_serve_callbacks.cpp"
TRIALS = 1000


def query(ctx):
    ctx.write(ctx.r(4), ctx.rng.choice([0, 1, 2, 0x100, 0x80000000, 0xFFFFFFFF]).to_bytes(4, "big"))


CALLS = {0x8225FFF8: model(query, args=("r3", "r4"))}


def inputs(t):
    blender = t.alloc(0xB0, "blender")
    t.w32(blender + 0x6C, t.rng.choice([0, 0, 1, 4, 0x100, 0xFFFFFFFF]))
    t.args(r3=blender)
