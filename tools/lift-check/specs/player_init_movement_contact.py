"""0x82195D50: mover/position/float arguments all reach the target setup."""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _player_mover_callers_common import *

FUNCTION = "pongPlayer::InitMovementAndContact"
ADDRESS = 0x82195D50
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000


def matrix(ctx):
    ctx.write(ctx.r(3), struct.pack(">16f", *[ctx.rng.uniform(-4, 4) for _ in range(16)]))
    ctx.ret(r3=ctx.r(3))


CALLS = {
    0x82195C00: stub(ret="void"),
    0x82195B60: stub(ret=lambda c: c.rng.randrange(2)),
    0x820CAC78: model(matrix, args=("r3", "r4", "r5")),
    0x821A5DF8: stub(ret=lambda c: c.rng.randrange(2), args=("r3", "r4", "f1", "f2"), deref={"r4": 16}),
}


def inputs(t):
    t.args(r3=player(t))
