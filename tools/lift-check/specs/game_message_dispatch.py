"""0x8225E7F8: category/mask gates and registry/message changes by receivers."""
import struct
from liftcheck.spec import *

FUNCTION = "DispatchGameMessage"
ADDRESS = 0x8225E7F8
SOURCE = "src/game/game_message.cpp"
TRIALS = 1000


def receive(c):
    receiver, message = c.r(3), c.r(4)
    calls = int.from_bytes(c.read(receiver + 4, 4), "big")
    c.write(receiver + 4, struct.pack(">I", calls + 1))
    c.write(receiver + 8, c.read(message, 4))
    # The category is snapshotted, while the flags and registry count stay live.
    old_id = int.from_bytes(c.read(message, 2), "big")
    c.write(message, struct.pack(">H", old_id ^ 0xF800))
    c.write(message + 2, bytes([c.rng.choice([0, 1, 0x40, 0x80, 0xFF])]))
    if c.rng.randrange(3) == 0:
        c.write(0x825F3864, bytes(4))


CALLS = {"sink.vfn_1": model(receive, args=("r3", "r4"))}


def inputs(t):
    message = t.alloc(16, "message")
    event_id = t.rng.getrandbits(16)
    category = 1 << (event_id >> 11)
    t.w16(message, event_id)
    t.w8(message + 2, t.rng.choice([0, 1, 0x20, 0x40, 0x80, 0xFF]))
    count = t.rng.choice([0, 1, 2, 4, 6])
    t.w32(0x825F3864, count)
    vtable = t.vtable("sink", slots=2)
    for i in range(6):
        sink = t.alloc(16, "sink", fill="zero")
        t.w32(sink, vtable)
        t.w32(0x825F3868 + 4 * i, sink)
        mask = t.rng.choice([0, category, category | 0x80000000, t.rng.getrandbits(32)])
        t.w32(0x825F3968 + 4 * i, mask)
        t.w8(0x825F3A68 + i, t.rng.choice([0, 1, 0x20, 0x40, 0x80, 0xFF]))
    t.args(r3=message)
