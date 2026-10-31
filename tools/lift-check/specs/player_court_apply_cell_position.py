"""Correct grid-cell argument and a four-lane VMX position update."""
from liftcheck.spec import *
FUNCTION = "pongPlayer::UpdatePositionFromSwingTarget"
ADDRESS = 0x8219E6D8
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 512

def position(ctx):
    import struct
    values = [0, 0x80000000, 1, 0x80000001, 0x007fffff, 0x807fffff,
              0x00800000, 0x80800000, 0x3f800000, 0xbf800000, 0x7fc00000]
    result = ctx.r(3) + 16
    ctx.write(result, b"".join(struct.pack(">I", ctx.rng.choice(values)) for _ in range(4)))
    ctx.ret(r3=result)

CALLS = {"pongPlayer_E7B0_g": model(position, args=("r3",))}

def inputs(t):
    self = t.alloc(0xc00, "target")
    t.w32(self + 0x3b4, t.rng.randrange(3))
    t.w32(self + 0x3b8, t.rng.randrange(3))
    for i in range(4):
        t.w32(self + 0x370 + i * 4, t.rng.choice([0, 1, 0x80000001, 0x3f800000, 0xbf800000, 0x7fc00000]))
    t.args(r3=self)
