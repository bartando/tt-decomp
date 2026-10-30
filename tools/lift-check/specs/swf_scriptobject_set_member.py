"""Script setter converts the tagged key, inserts at object+4, and returns 1.

Run original key conversion for direct strings and finite chunk chains. Model
only insertion, comparing all arguments, converted text and both value words;
arbitrary insertion returns must not leak through as the setter's status.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfSCRIPTOBJECT::SetMember"
ADDRESS = 0x823FC8A8
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
RET = "r3"


def _insert(ctx):
    ctx.write(ctx.r(3), ctx.read(ctx.r(5), 8))
    ctx.ret(r3=ctx.rng.getrandbits(32))


CALLS = {0x823FA768: run(),
         0x823FB258: model(_insert, args=("r3", "r4", "r5"), deref={"r5": 8})}


def inputs(t):
    rng = t.rng
    obj = t.alloc(16, "object")
    key = t.alloc(8, "key")
    value = t.alloc(8, "value")
    text = rng.choice((b"", b"this", b"prototype", b"custom", b"CaseSensitive", b"key_" * 80))
    if rng.randrange(2):
        t.w32(key, t.alloc(len(text) + 1, "keyText", fill=text + b"\0"))
        t.w32(key + 4, 1)
    else:
        head = 0
        for chunk in reversed([text[i:i + 12] for i in range(0, len(text), 12)] or [b""]):
            node = t.alloc(16, "keyChunk", fill=chunk.ljust(12, b"\0"))
            t.w32(node + 12, head)
            head = node
        t.w32(key, head)
        t.w32(key + 4, 0)
    t.args(r3=obj, r4=key, r5=value)
