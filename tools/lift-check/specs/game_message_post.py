"""0x8225E6E0: queued/inline packets, low-byte counts and payload preservation.

Positive-length immediate messages supply a payload: otherwise the original
hands undefined stack bytes to receivers. The port zeros that invalid payload.
Queued null payloads are covered and must retain existing queue words.
"""
import struct
from liftcheck.spec import *

FUNCTION = "PostGameMessage"
ADDRESS = 0x8225E6E0
SOURCE = "src/game/game_message.cpp"
TRIALS = 1000


def lock(c):
    assert c.r(3) == 0x82619DA0
    words = int.from_bytes(c.read(0x825F3860, 4), "big")
    c.write(0x825F3860, struct.pack(">I", words + 1))


def consume(c):
    packet = c.r(3)
    count = c.read(packet + 3, 1)[0]
    # Observe the complete defined packet, independent of compiler stack layout.
    c.write(0x825F3AA8, c.read(packet, 4 + count * 4))
    words = int.from_bytes(c.read(0x825F3860, 4), "big")
    c.write(0x825F3860, struct.pack(">I", words + 7))


CALLS = {
    0x82569394: run(transparent=True, args=()),  # Original variable-stack probe.
    0x821880D0: run(),
    0x82188130: run(),
    0x82585E0C: model(lock, args=("r3",)),
    0x82585DFC: stub(ret="void", args=("r3",)),
    0x8225E7F8: model(consume, args=("r3",)),
}


def inputs(t):
    rng = t.rng
    flags = rng.choice([0, 1, 0x3F, 0x40, 0x41, 0x80, 0xC0, 0x100, 0x140, 0xFFFFFFFF])
    count = rng.choice([0, 1, 2, 7, 255, 256, 257, 0xFFFFFFFF, rng.getrandbits(32)])
    if t.index == 0:
        count = 256  # Low-byte wrap; also makes the full-count mutant fail safely.
    payload = t.alloc(1020, "payload")
    if not (flags & 0x40) and rng.randrange(3) == 0:
        payload = 0
    t.w32(0x825F3860, rng.randrange(500))
    t.w8(0x825EE297, rng.randrange(2))
    t.put(0x825F3AA8, rng.randbytes(8192))
    t.args(r3=rng.getrandbits(32), r4=flags, r5=count, r6=payload)
