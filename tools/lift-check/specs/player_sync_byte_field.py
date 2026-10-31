"""0x82199108: two-argument ABI and source reload after the dirty callback."""
from liftcheck.spec import *

FUNCTION = "pongPlayer::SyncByteField"
ADDRESS = 0x82199108
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000


def callback(ctx):
    source = int.from_bytes(ctx.read(ctx.r(3), 4), "big")
    ctx.write(source, ctx.read(ctx.r(3) + 4, 1))


CALLS = {"dirty": model(callback, args=("r3",))}


def inputs(t):
    target = t.alloc(16, "trackedByte")
    source = target if t.index % 17 == 16 else t.alloc(4, "source")
    argument = t.alloc(8, "callbackData")
    old = t.index % 256
    new = old if t.index % 4 == 0 else (old + 1) % 256
    t.w8(target, old)
    t.w8(source, new)
    t.w32(argument, source)
    t.w8(argument + 4, (new + 1) % 256)
    t.w32(target + 4, argument)
    t.w32(target + 8, 0 if t.index % 3 == 0 else t.fake_fn("dirty"))
    t.args(r3=target, r4=source)
