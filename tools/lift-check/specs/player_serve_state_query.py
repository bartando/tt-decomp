"""Null result, input low-byte gate, and serve state reread after polling."""
from liftcheck.spec import *
FUNCTION = "io_8A48"
ADDRESS = 0x82198A48
SOURCE = "src/game/player/pong_gameplay_queries.cpp"
TRIALS = 512

def poll(ctx):
    data = ctx.r(3)
    player = int.from_bytes(ctx.read(data, 4), "big")
    ctx.write(player + 0x17ec, ctx.read(data + 4, 4))
    ctx.ret(r3=int.from_bytes(ctx.read(data + 8, 4), "big"))

CALLS = {"io_Input_poll_9D68": model(poll, args=("r3",), preserves=("r4", "r9"))}
# The original leaf poll writes r3/r5/r6/r8/r10/r11, leaving r4/r9 intact.

def inputs(t):
    player = t.alloc(0x1800, "player")
    result = t.alloc(4, "answer") if t.index % 4 else 0
    data = t.alloc(16, "input gate")
    t.w32(data, player)
    t.w32(data + 4, t.rng.choice([0, 1, -1, 2, 0x80000000]))
    t.w32(data + 8, t.rng.choice([0, 1, 2, 255, 256, 0x80000000, 0xffffff01]))
    t.w32(0x825eab28, data)
    t.args(r3=player, r4=result)
