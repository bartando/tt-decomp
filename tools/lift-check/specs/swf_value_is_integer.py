"""Retail's integer classification, including its permissive string rules.

Chunk inputs fit the original 40-byte stack buffer (at most three chunks).
The actual CRT strchr runs on both sides. No ignored memory or tolerance.
"""
from liftcheck.spec import *

FUNCTION = "swfValueIsInteger"
ADDRESS = 0x823FA4C8
SOURCE = "src/rage/swf_value_helpers.cpp"
TRIALS = 600
EXTERNS = {"strchr": 0x824321B0}
CALLS = {0x824321B0: run()}


def inputs(t):
    rng = t.rng
    value = t.alloc(8, "value")
    tag = t.index % 10
    t.w32(value + 4, tag)
    if tag <= 1:
        text = rng.choice((b"", b"garbage", b"-42", b"12.", b"12.0", b"12.0000",
                           b"12.0001", b"12.0.0", b".0", b".00x", b" 1e3", b"nan",
                           b"x.00000000000000000000000001", b"0.\xff"))
        if rng.randrange(8) == 0:
            head = 0
        elif tag == 1:
            head = t.alloc(len(text) + 1, "text", fill=text + b"\0")
        else:
            head = 0
            for chunk in reversed([text[i:i + 12] for i in range(0, len(text), 12)] or [b""]):
                node = t.alloc(16, "chunk", fill=chunk.ljust(12, b"\0"))
                t.w32(node + 12, head)
                head = node
        t.w32(value, head)
    t.args(r3=value)
