"""0x821C9870: canonical message copies the column word before dirty sync."""
from liftcheck.spec import *

FUNCTION = "pongPlayer::NotifySlotChangeAndSync"
ADDRESS = 0x821C9870
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000
EXTERNS = {"g_kSlotSpeedLookup": 0x825C76DC}
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
    slot = t.index % 2
    column = (t.index // 2) % 3
    for player in range(2):
        for entry in range(3):
            field = slots + 0xAC + player * 36 + entry * 12
            t.w8(field, t.rng.choice([0, 0, 1, 255]))
            t.w32(field + 4, 0)
            t.w32(field + 8, 0)
    t.w8(slots + 288 + slot, 0)
    t.floats(t.sym("g_kSlotSpeedLookup"), 3, 1, 20)
    EXPECTED_PAYLOAD = column.to_bytes(4, "big")
    t.args(r3=slots, r4=slot, r5=column)
