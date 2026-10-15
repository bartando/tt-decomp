"""gmBallNode::Initialize (0x82280D48): physics setup, effects, message sinks, pace settings.

The fxBallTrail and fxBallSplash2D constructors and the splash reset run as the
original code; their virtual calls land on stubs at the real vtable targets.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode::Initialize"
ADDRESS = 0x82280D48
SOURCE = "src/game/ball/pong_ball.cpp"

# The message-sink list's names carry conflicting markers elsewhere in src/.
EXTERNS = {
    "g_eventQueueIndex": 0x825F3864,
    "g_eventQueuePtrs": 0x825F3868,
    "g_eventQueueMasks": 0x825F3968,
    "g_eventQueueFlags": 0x825F3A68,
}

SDA = 0x82600000            # the lift reads r13 through g_sda_base, which lives here

CALLS = {
    0x822E2E60: stub(ret="void"),                 # fiAssetFolders_Push
    0x823D9160: stub(ret="void"),                 # sgPhysicalObject_Initialize
    0x82282318: stub(ret="void"),                 # SetScale
    0x820C0038: stub(ret="void"),                 # sysMemAllocator_InitMainThread
    "alloc.vfn_1": alloc(size_reg="r4", args=("r3", "r4", "r5")),
    0x822812A8: run(),                            # fxBallTrail ctor
    0x82381150: stub(ret=lambda ctx: ctx.r(3)),   # fxBallTrail slot 2 (reset); the ctor relies on r3 surviving
    0x82381208: stub(ret="void", args=("r3", "r4", "r5", "r6")),   # fxBallTrail slot 3 (setup)
    0x82388978: stub(ret="void"),                 # fxBallSpinTex slot 2
    0x82280898: stub(ret="void", args=("r3", "r4")),   # fxBallSpinTex slot 4 (texture)
    0x82389BD8: run(),                            # fxBallSplash2D reset
    "arch.vfn_7": stub(ret=lambda ctx: ctx.rng.uniform(0.001, 1.0)),
    "arch.vfn_14": stub(ret="void", deref={"r4": 12}),
    "level.vfn_4": alloc(size_reg=None, size=0x100, args=("r3", "r4")),
    0x8215A2F8: stub(),                           # game_A2F8("Ball_Color", 1)
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    t.wf32(node + 0x8C, rng.choice([rng.uniform(-1, 12), 0.1, 10.0, 0.05, 20.0]))   # scale
    t.wf32(node + 0x84, rng.choice([rng.uniform(-2, 12), 0.0, 10.0]))               # popFlyMinHeight

    inst = t.alloc(0x100, "inst")
    arch = t.alloc(0x40, "arch")
    bound = t.alloc(0x80, "bound")
    t.w32(node + 0x74, inst)
    t.w32(inst + 4, arch)
    index = rng.randrange(16)
    t.w16(inst + 8, index)
    t.w32(arch, t.vtable("arch"))
    t.w32(arch + 0x0C, bound)
    t.wf32(bound + 8, rng.uniform(0.01, 0.1))
    draw = t.alloc(0x80, "drawInst")
    t.w32(node + 0x7C, draw)

    sim = t.alloc(0x10, "sim")
    level = t.alloc(0x20, "level")
    states = t.alloc(16, "states", fill=bytes(rng.choice([0, 8, 0x10, 0xF8]) for _ in range(16)))
    t.w32(0x825F5BD0, sim)
    t.w32(sim + 4, level)
    t.w32(level, t.vtable("level"))
    t.w32(level + 0x1C, states)

    slot = t.alloc(4, "ballInstSlot")
    t.w32(0x8271A2F4, slot)

    sda = t.alloc(0x10, "sda", fill="zero")
    tls = t.alloc(0x10, "tls", fill="zero")
    allocator = t.alloc(0x10, "allocator", fill="zero")
    t.w32(sda, tls)
    t.w32(tls + 4, allocator)
    t.w32(allocator, t.vtable("alloc"))
    t.w32(SDA, sda)

    textures = t.alloc(0x30, "textures")
    t.w32(textures + 0x2C, rng.randrange(3))
    t.w32(0x8271A7F8, textures)

    t.w32(0x825F3864, rng.randrange(8))           # message-sink count

    holder = t.alloc(0x10, "holder")
    target = t.alloc(0x470, "holderTarget")
    t.w32(holder + 8, target)
    t.w32(0x826063C8, holder)

    ctx = t.alloc(0x120, "context")
    t.w32(0x825EAB28, ctx)

    t.args(r3=node, r13=sda)
