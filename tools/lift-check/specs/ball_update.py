"""gmBallNode::Update (0x82281630): flag71 history, replay hand-off, velocity, effect
hold, the trail frame built from the ball's movement, audio emitters, fxScale fade."""
import math
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode::Update"
ADDRESS = 0x82281630
SOURCE = "src/game/ball/pong_ball.cpp"
FTOL = 1e-5

# RTDynamicCast's marker sits on its declaration's second line; ph_update_object.cpp
# marks g_phFrameIndex at 0x825C4898 as well. clang keeps a libm sqrtf call for the
# errno path (negative input, never taken here): park it on the image header and
# model it, out of the trace.
SQRTF = 0x82000000
EXTERNS = {"RTDynamicCast": 0x82430978, "g_phFrameIndex": 0x826065DC, "sqrtf": SQRTF}

GAME_STATE = 0x8271A2F8
BALL_SLOT = 0x8271A2F4


def _rd32(ctx, a):
    return struct.unpack(">I", bytes(ctx.read(a, 4)))[0]


def _cast(ctx):
    """RTDynamicCast(phInst -> pongBallInstance): the instance, or (only when the
    prediction branch will run, so the else branch never sees null) sometimes null."""
    gs = _rd32(ctx, GAME_STATE)
    count = struct.unpack(">i", bytes(ctx.read(_rd32(ctx, gs + 0x14) + 0x25A8, 4)))[0]
    if count > 0 and ctx.rng.random() < 0.25:
        return 0
    return ctx.r(3)


def _predict(ctx):
    """pg_70C8_g: the physics moves the published ball."""
    inst = _rd32(ctx, _rd32(ctx, BALL_SLOT))
    for k in range(3):
        old = struct.unpack(">f", bytes(ctx.read(inst + 0x40 + 4 * k, 4)))[0]
        ctx.write(inst + 0x40 + 4 * k, struct.pack(">f", old + ctx.rng.uniform(-0.3, 0.3)))


CALLS = {
    "node.vfn_34": stub(ret=lambda ctx: ctx.rng.choice([0, 1])),
    0x82282110: stub(ret="void"),                       # gmBallNode_UpdateReplay
    0x821D3E10: stub(ret="void"),                       # rage_3E10
    "level.vfn_4": stub(ret=lambda ctx: ctx.rng.choice([0, 0x1000, 0x2000])),
    "trail.vfn_2": stub(ret="void"),
    "trail.vfn_4": stub(ret="void", args=("r3",), deref={"r4": 16, "r5": 12}),
    "spin.vfn_3": stub(ret="void"),
    "spin.vfn_5": stub(ret="void"),
    0x82389BD8: run(),                                  # splash reset
    0x82389FD8: stub(ret="void"),                       # splash update
    0x82430978: stub(ret=_cast),
    0x822870C8: model(_predict),
    0x820D2038: stub(ret="void"),                       # util_2038: fills the point
    "ballInst.vfn_3": stub(ret="void", args=("r3", "r4")),
    0x82160C98: run(),      # pg_0C98_g: leaf; Update relies on it leaving r4 alone
    SQRTF: model(lambda ctx: ctx.ret(f1=math.sqrt(ctx.f(1)) if ctx.f(1) >= 0 else math.nan),
                 transparent=True),
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    t.w32(node, t.vtable("node", 40))
    t.floats(node + 0xF0, 20, -3, 3)                    # lastMatrix, velocity
    # fxScale fade: idle, running, or about to finish
    t.floats(node + 0x94, 3, 0, 2)
    t.wf32(node + 0xA0, rng.choice([0.5, 0.01, 2.0]))
    t.wf32(node + 0xA4, rng.choice([-1.0, 0.0, 0.2, 0.49, 3.0]))
    t.w8(node + 0xA8, rng.choice([0, 1]))

    def ballinst(name):
        p = t.alloc(0xD0, name)
        t.w32(p, t.vtable("ballInst"))
        t.floats(p + 0x10, 16, -2, 2)
        t.wf32(p + 0x4C, rng.choice([1.0, 0.0]))
        t.w16(p + 8, rng.randrange(16))
        if rng.random() < 0.7:
            audio = t.alloc(0x340, name + ".audio")
            t.w8(audio + 0x338, rng.choice([0, 1]))
            t.wf32(audio + 0x314, rng.uniform(-1, 1))
            t.w32(p + 0x58, audio)
        else:
            t.w32(p + 0x58, 0)
        return p

    inst = ballinst("inst")
    published = inst if rng.random() < 0.8 else ballinst("published")
    t.w32(node + 0x74, inst)
    slot = t.alloc(4, "ballSlot")
    t.w32(slot, published)
    t.w32(BALL_SLOT, slot)

    def obj(off, name, size=0x20, vt=True):
        if rng.random() < 0.75:
            p = t.alloc(size, name)
            if vt:
                t.w32(p, t.vtable(name))
            t.w32(node + off, p)
        else:
            t.w32(node + off, 0)

    obj(0xAC, "trail")
    obj(0xB0, "trail")
    obj(0xB8, "spin")
    obj(0xBC, "splash", size=0x240, vt=False)

    history = t.alloc(0x460, "history", fill="zero")
    t.w32(0x825EB2FC, history)
    t.w32(0x826065DC, rng.randrange(16))                 # g_phFrameIndex

    replay = t.alloc(0x68D00, "replay", fill="zero")
    t.w32(replay + 0x68CF0, rng.choice([0, 0, 0, 0, 1, 2]))
    t.w32(0x8271A2EC, replay)

    sim = t.alloc(0x10, "sim")
    level = t.alloc(0x20, "level")
    states = t.alloc(16, "states", fill=bytes(rng.choice([0, 1, 8]) for _ in range(16)))
    t.w32(0x825F5BD0, sim)
    t.w32(sim + 4, level)
    t.w32(level, t.vtable("level"))
    t.w32(level + 0x1C, states)

    gs = t.alloc(0x40, "gameState")
    predict = t.alloc(0x25B0, "predict", fill="zero")
    t.w32(gs + 0x14, predict)
    t.w32(predict + 0x25A8, rng.choice([-1, 0, 1, 1, 7]))
    t.w32(GAME_STATE, gs)

    t.w8(0x8260656D, rng.choice([0, 1]))
    t.wf32(0x825CAEC0, rng.choice([1 / 60, 1 / 30, 0.02]))   # frame seconds
    t.args(r3=node)
