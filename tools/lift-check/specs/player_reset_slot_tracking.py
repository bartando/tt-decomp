"""0x821C9918: first active column is a copied payload word, then three clears."""
from liftcheck.spec import *

FUNCTION = "pongPlayer::ResetButtonSlotTrackingData"
ADDRESS = 0x821C9918
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000
EXPECTED_PAYLOAD = b""


def post(ctx):
    assert ctx.r(5) == 1 and ctx.in_stack(ctx.r(6))
    assert ctx.read(ctx.r(6), 4) == EXPECTED_PAYLOAD


CALLS = {
    "PostGameMessage": model(post, args=("r3", "r4", "r5", "r6")),
    0x82199108: run(args=("r3", "r4"), deref={"r4": 1}),
}


def inputs(t):
    global EXPECTED_PAYLOAD
    slots = t.alloc(0x180, "slots")
    slot = t.rng.randrange(2)
    flags = t.index % 8
    for player in range(2):
        for entry in range(3):
            field = slots + 0xAC + player * 36 + entry * 12
            t.w8(field, t.rng.choice([1, 255]) if flags & (1 << entry) else 0)
            t.w32(field + 4, 0)
            t.w32(field + 8, 0)
    first = next((index for index in range(3) if flags & (1 << index)), 0)
    EXPECTED_PAYLOAD = first.to_bytes(4, "big")
    t.args(r3=slots, r4=slot)
