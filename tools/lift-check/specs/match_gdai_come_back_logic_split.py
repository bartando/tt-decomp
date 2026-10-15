"""gdaiComeBackLogic::SplitLeadAndDeficit (slot 3, 0x821EA1B8).

Children carry a kind byte at +0x0C (0 other, 1 gdaiDeficit, 2 gdaiLead) that
the fake slot 20 (IsA) answers from; slot 19 (name) returns a string at +0x30.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gdaiComeBackLogic_SplitLeadAndDeficit"
ADDRESS = 0x821EA1B8
SOURCE = "src/game/match/pong_match.cpp"

DEFICIT, LEAD = 0x825C60CC, 0x825C60D0   # each word holds its own address
EXTERNS = {"g_gdaiDeficitTypeId": DEFICIT, "g_gdaiLeadTypeId": LEAD,
           "game_DB80": 0x821EDB80, "nop_8240E6D0": 0x8240E6D0}
MAX_NODES = 12


def _is_a(ctx):
    kind = ctx.read(ctx.r(3) + 0x0C, 1)[0]
    ctx.ret(r3=int((ctx.r(4), kind) in ((DEFICIT, 1), (LEAD, 2))))


def _name(ctx):
    ctx.ret(r3=ctx.r(3) + 0x30)


def _reserve(ctx):
    arr, n = ctx.r(3), ctx.r(4)
    assert 0 < n <= MAX_NODES, f"reserve {n}"
    ctx.write(arr, struct.pack(">I", ctx.alloc(4 * n)))
    ctx.write(arr + 6, struct.pack(">H", n))


CALLS = {
    0x821EDB80: model(_reserve),
    # variadic debug log: compare the format's bytes and the name pointer
    0x8240E6D0: stub(ret="void", args=("r4",), deref={"r3": 41}),
}
for _i in range(MAX_NODES):
    CALLS[f"node{_i}.vfn_20"] = model(_is_a)
    CALLS[f"node{_i}.vfn_19"] = model(_name)


def inputs(t):
    rng = t.rng
    logic = t.alloc(0x20, "comeBackLogic")
    for off in (0x10, 0x18):           # arrays: random data/capacity, count 0
        t.w16(logic + off + 4, 0)
    n = rng.choice([0, 1, 2, 3, 5, rng.randrange(MAX_NODES + 1)])
    nxt = 0
    for i in reversed(range(n)):
        node = t.alloc(0x40, f"node{i}")
        t.w32(node, t.vtable(f"node{i}", 24))
        t.w32(node + 0x08, nxt)
        t.w8(node + 0x0C, rng.choice([0, 1, 1, 2, 2]))
        t.put(node + 0x30, f"gdaiNode{i}\0".encode())
        nxt = node
    t.w32(logic + 0x0C, nxt)
    t.args(r3=logic)
