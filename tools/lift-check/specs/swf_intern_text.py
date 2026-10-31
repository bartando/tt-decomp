"""All table states: existing entry, first hole, full, empty, and truncation.

The original bounded CRT copy executes on both sides; table bytes are exact.
"""
from liftcheck.spec import *

FUNCTION = "swfInternText"
ADDRESS = 0x823F9FB0
SOURCE = "src/rage/swf_text.cpp"
TRIALS = 400
CALLS = {0x82430120: run()}


def inputs(t):
    rng = t.rng
    table = 0x82602848  # g_swfInternedText
    slots = [bytearray((f"slot_{i:03d}".encode() + b"\0" + rng.randbytes(55))) for i in range(128)]
    mode = t.index % 6
    if mode in (0, 1, 2, 3, 5):
        for i in rng.sample(range(128), rng.randrange(1, 70)):
            slots[i][0] = 0
    if mode in (0, 3):
        index = rng.choice([i for i in range(128) if slots[i][0] != 0])
        text = bytes(slots[index]).split(b"\0")[0]
    elif mode == 1:
        text = b""
    elif mode == 2:
        text = b"x" * rng.choice((63, 64, 65, 100, 1000))
    else:
        text = b"new-entry"
    t.put(table, b"".join(slots))
    source = t.alloc(len(text) + 1, "text", fill=text + b"\0")
    t.args(r3=source)
