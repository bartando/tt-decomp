"""Script-object member lookup, including prototype allocation and lookup order.

Limits: keys use direct strings or finite, disjoint string chunks; the conversion
helper runs as original code. Lookup is modelled as returning the pointer stored in
each table, with its table and converted key compared at every call. The pool must
have a non-null free object: the original dereferences it before checking for null.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfSCRIPTOBJECT::GetMember"
ADDRESS = 0x823FBFC0
SOURCE = "src/rage/swf.cpp"
TRIALS = 600
EXTERNS = {"swfSymtab_Lookup": 0x823FB3B8}


def _lookup(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3), 4), "big"))


CALLS = {
    0x823FA768: run(),
    0x823FB3B8: model(_lookup, args=("r3", "r4"), preserves=("r4",)),
}


def inputs(t):
    rng = t.rng
    obj = t.alloc(16, "object")
    result = t.alloc(8, "result")
    global_table = t.alloc(4, "globalTable")
    scope = t.alloc(16, "scope")
    tables = (obj + 4, global_table, scope + 4)
    for i, table in enumerate(tables):
        entry = t.alloc(8, f"entry{i}")
        t.w32(table, rng.choice((0, entry)))
    t.w32(0x82602818, global_table)
    t.w32(0x8260282C, scope)
    t.w32(obj + 12, rng.choice((0, t.alloc(16, "prototype"))))

    pool = t.alloc(16, "pool")
    free = t.alloc(16, "freeObject")
    t.w32(free, t.alloc(16, "nextFree"))
    t.w16(pool + 6, rng.choice((0, 1, 0xFFFF, rng.randrange(0x10000))))
    t.w32(pool + 12, free)
    t.w32(0x82604C60, pool)

    text = rng.choice(("this", "prototype", "custom", "", "THIS", "prototypeX",
                       "thisX", "long_property_" * 8)).encode()
    key = t.alloc(8, "key")
    if rng.randrange(2):
        t.w32(key, t.alloc(len(text) + 1, "keyText", fill=text + b"\0"))
        t.w32(key + 4, 1)
    else:
        chunks = [text[i:i + 12] for i in range(0, len(text), 12)] or [b""]
        head = 0
        for chunk in reversed(chunks):
            node = t.alloc(16, "keyChunk", fill=chunk.ljust(12, b"\0"))
            t.w32(node + 12, head)
            head = node
        t.w32(key, head)
        t.w32(key + 4, 0)
    t.args(r3=obj, r4=key, r5=result)
