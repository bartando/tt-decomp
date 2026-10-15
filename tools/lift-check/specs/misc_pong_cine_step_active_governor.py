"""pongCineCamMgr::StepActiveGovernor: picks governor A (mode 1, with the shot
sample and condition-14 refresh) or B (modes 2/3), steps its camera machine and
applies the new node. Callees are stubbed; the condition evaluator's out value
is random, so both the > 0 and <= 0 cases come up."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCineCamMgr::StepActiveGovernor"
ADDRESS = 0x82167558
SOURCE = "src/game/camera/pong_camera.cpp"
FTOL = 0


def cond_eval(ctx):
    """0x82217278(evaluator, key, 14, &value, 1): writes value->value, returns bool."""
    p = ctx.r(6)
    import struct
    v = ctx.rng.choice([0.0, -1.0, ctx.rng.uniform(0.01, 5.0), ctx.rng.uniform(0.01, 5.0)])
    ctx.write(p + 4, struct.pack(">f", v))
    return ctx.rng.choice([0, 1])


def coin(ctx):
    return ctx.rng.choice([0, 1])


CALLS = {
    0x821F7818: stub(ret="void"),
    0x821F78D8: stub(ret="void"),
    0x82217278: stub(ret=cond_eval, args=("r3", "r5", "r7"), deref={"r4": 8, "r6": 8}, auto_out=False),
    0x82167EA8: stub(ret=coin, args=("r3", "r4", "r5")),
    0x82168CB0: stub(ret="void"),
}


def governor(t, name):
    g = t.alloc(0x28, name)
    t.w32(g, t.vtable(name, 2))
    t.w32(g + 4, t.alloc(0x10, f"{name}.machine"))
    t.floats(g + 8, 2, 0.0, 2.0)
    return g


def inputs(t):
    rng = t.rng
    cine = t.alloc(0x18, "cine")
    t.w32(cine + 8, rng.choice([0, 1, 1, 1, 2, 3, 4, -1]))
    t.w32(cine + 0x10, governor(t, "governorA"))
    t.w32(cine + 0x14, governor(t, "governorB"))
    gd = t.alloc(0x68D20, "gameData", fill="zero")
    t.floats(gd + 0xE900, 4, -10, 10)
    t.wf32(gd + 0x68D04, rng.uniform(0, 1))
    t.w32(gd + 0x68D18, t.alloc(0x10, "evaluator"))
    t.w32(0x8271A2EC, gd)
    for a in (0x82619AD0, 0x82619AE0):
        for k in range(4):
            t.wf32(a + 4 * k, rng.uniform(-10, 10))
    t.wf32(0x826064C8, rng.uniform(0, 1))
    t.args(r3=cine)
