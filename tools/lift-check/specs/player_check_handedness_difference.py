"""pongPlayer_04B0_g (0x821E04B0), formerly pongPlayer::CheckHandednessDifference.

Really (pad record, button id): 0x821E0270 remaps the button through the pad's
handedness flags (+0x04..+0x07), then bit 7 of bytes 0 and 3 of the button's
entry in the table at pad+0x31C are compared. The original keeps r7 across
that leaf call, so it runs as is.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongPlayer_04B0_g"
ADDRESS = 0x821E04B0
SOURCE = "src/game/player/pong_player.cpp"

CALLS = {0x821E0270: run()}


def inputs(t):
    rng = t.rng
    pad = t.alloc(0x328, "pad", fill="zero")
    for k in range(4, 8):
        t.w8(pad + k, rng.choice([0, 1]))
    t.w32(pad + 0x31C, t.alloc(0x100, "buttons"))
    t.args(r3=pad, r4=rng.randrange(0x20, 0x3A))
