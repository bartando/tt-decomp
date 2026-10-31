"""0x821CE0F0: active/inactive queues, signed counts, sparse record resets."""
from liftcheck.spec import *

FUNCTION = "game_E0F0"
ADDRESS = 0x821CE0F0
SOURCE = "src/game/player/player_serve_callbacks.cpp"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x68D20, "inputEvents")
    t.w8(obj + 0x68CF9, rng.choice([0, 0, 1, 2, 0xFF]))
    queue = t.alloc(0x24, "queue")
    records = t.alloc(0x14 * 12, "records")
    t.w32(queue + 0x08, rng.choice([-2, -1, 0, 1, 2, 5, 12]))
    t.w32(queue + 0x0C, records)
    t.w32(obj + 0x68D18, queue)
    slots = t.alloc(0x0C, "slots")
    entries = t.alloc(8 * 12, "entries")
    t.w32(slots + 0x04, rng.choice([-2, -1, 0, 1, 2, 5, 12]))
    t.w32(slots + 0x08, entries)
    t.w32(obj + 0x68D1C, slots)
    t.args(r3=obj)
