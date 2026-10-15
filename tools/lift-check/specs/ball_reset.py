"""gmBallNode::Reset (0x82281408): back on the node's matrix, out of the level, effects
cleared, ball colour and scale reapplied."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode::Reset"
ADDRESS = 0x82281408
SOURCE = "src/game/ball/pong_ball.cpp"

# The symbol map files the name game_3860 under 0x82483860 too; the lift's marker means 0x821D3860.
EXTERNS = {"game_3860": 0x821D3860}

CALLS = {
    "node.vfn_32": stub(ret="void", args=("r3", "r4")),
    "node.vfn_35": stub(ret="void", args=("r3", "r4")),
    "trail.vfn_2": stub(ret="void"),
    "spin.vfn_3": stub(ret="void"),
    0x82389BD8: run(),                      # fxBallSplash2D reset
    0x822C4B60: stub(ret="void"),           # game_4B60
    0x821D3860: stub(ret="void"),           # game_3860
    0x821C9D68: run(),                      # io_Input_poll_9D68: leaf; Reset keeps f1 and r7 across it
    0x82282318: stub(ret="void"),           # SetScale
    # pg_C2A0_g walks a list. Run it: Reset relies on it leaving r8 alone (MSVC's
    # link-time codegen knows it does), and a stub clobbers r8.
    0x821DC2A0: run(),
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    t.w32(node, t.vtable("node", 40))

    def obj(off, name, size=0x20):
        if rng.random() < 0.7:
            p = t.alloc(size, name)
            t.w32(p, t.vtable(name))
            t.w32(node + off, p)
        else:
            t.w32(node + off, 0)

    obj(0xAC, "trail")
    obj(0xB0, "trail")
    obj(0xB8, "spin")
    obj(0xBC, "splash", size=0x240)

    inst = t.alloc(0x60, "inst")
    arch = t.alloc(0x20, "arch")
    t.w32(node + 0x74, inst)
    t.w32(inst + 4, arch)
    t.w16(inst + 8, rng.randrange(16))
    t.w32(inst + 0x58, t.alloc(0x340, "audio") if rng.random() < 0.6 else 0)

    level = t.alloc(0x20, "level")
    states = t.alloc(16, "states", fill=bytes(rng.choice([0, 1, 8, 0x0F]) for _ in range(16)))
    t.w32(level + 0x1C, states)
    t.w32(0x826065E4, level)

    # *0x8271A310 -> +8 -> +0xC: a list linked through +8; the key is how many nodes to skip.
    nodes = [t.alloc(0x1720, f"record{k}") for k in range(3)]
    for k, rec in enumerate(nodes):
        t.floats(rec + 0x1710, 4, -2, 2)
        t.w32(rec + 8, nodes[k + 1] if k + 1 < len(nodes) else 0)
    root = t.alloc(0x10, "lookupRoot")
    holder = t.alloc(0x10, "lookupHolder")
    t.w32(root + 8, holder)
    t.w32(holder + 0xC, nodes[0])
    t.w32(0x8271A310, root)

    ctx = t.alloc(0x160, "context")
    for off in (0x14C, 0x14E):
        t.w8(ctx + off, rng.choice([0, 0, 1]))
    t.w32(ctx + 0x154, rng.choice([0, 0, 5]))
    t.w32(ctx + 0x28, rng.randrange(3))      # the lookup key
    t.w32(0x825EAB28, ctx)

    table = t.alloc(0x110, "shaderGlobals", fill="zero")
    entries = t.alloc(8 * 16, "entries")
    values = t.alloc(16 * 32, "values", fill="zero")
    t.w32(table + 0x100, entries)
    t.w32(table + 0x108, values)
    entry = rng.randrange(16)
    t.w32(entries + entry * 8 + 4, (rng.getrandbits(16) << 16) | rng.randrange(32))
    t.w32(node + 0x140, (entry << 18) | (rng.randrange(0x800) << 1) | rng.randrange(2))
    t.w32(0x825EBC40, table)

    t.w32(0x825C9A2C, rng.choice([0, 0, 1, -1]))
    t.w8(0x825C5EC8 + 0x30, rng.choice([0, 1]))
    t.w32(0x82606570, t.alloc(0x150, "activeBallNode"))
    t.args(r3=node)
