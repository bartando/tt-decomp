"""datParser::AddField (0x82177B60): pool or new record, space-stripped name, list append."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "datParser_AddField"
ADDRESS = 0x82177B60
SOURCE = "src/rage/data/dat_parser_fields.cpp"

CALLS = {
    "xe_EC88": alloc(size_reg="r3"),
}

REC = 0x58


def inputs(t):
    rng = t.rng
    parser = t.alloc(0x1658, "parser")
    used = rng.choice([0, 1, 5, 63, 64, 64, 70])
    t.w32(parser + 0x1654, used)
    t.w32(parser + 0x44, rng.randrange(100))
    # an existing list of 0..3 records (pool ones, or separate ones)
    n = rng.choice([0, 0, 1, 2, 3])
    prev = None
    head = 0
    for k in range(n):
        r = t.alloc(REC, f"rec{k}")
        t.w32(r + 0x54, 0)
        if prev is None:
            head = r
        else:
            t.w32(prev + 0x54, r)
        prev = r
    t.w32(parser + 0x4C, head)
    if used < 64:
        # the pool record about to be reused: its next link is left as is,
        # so keep it null (a stale link would make a cycle)
        t.w32(parser + 0x54 + used * REC + 0x54, 0)
    length = rng.choice([0, 1, 5, 62, 63, 64, 80])
    chars = bytes(rng.choice(b"abcXYZ_ 09") for _ in range(length)) + b"\0"
    name = t.alloc(len(chars), "name", fill=chars)
    t.args(r3=parser, r4=rng.getrandbits(32), r5=name, r6=rng.getrandbits(32))
