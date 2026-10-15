"""BallShot_Launch (0x822827E8): launch velocity and spin, per-shot gravity factor, prediction."""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "BallShot_Launch"
ADDRESS = 0x822827E8
SOURCE = "src/game/ball/ball_shot.cpp"

BALL_SLOT = 0x8271A2F4
LEVEL = 0x826065E4
INPUT = 0x825EAB28
GAME_STATE = 0x8271A2F8


def _fill_out(ctx, reg):
    a = ctx.r(reg)
    ctx.write(a, ctx.rng.randbytes(16))


def _spin_from_axis(ctx):
    _fill_out(ctx, 4)
    ctx.ret()


def _solve(ctx):
    _fill_out(ctx, 6)
    _fill_out(ctx, 7)
    ctx.ret(r3=ctx.rng.choice([0, 1, 2]))


_probe = [0]  # input block the model copies ProcessHit's arguments into (set per trial)


def _predict(ctx):
    """r6 is garbage on the original's side and vel/spin are stack temporaries, so
    copy what matters into the probe block, where the memory diff compares it."""
    probe = _probe[0]
    ctx.write(probe, bytes(ctx.read(ctx.r(4), 16)) + bytes(ctx.read(ctx.r(5), 16)))
    ctx.write(probe + 32, struct.pack(">IIIf", ctx.r(3), ctx.r(7), ctx.r(8), ctx.f(1)))
    ctx.ret()


_predict_model = model(_predict)
_predict_model.args = ("r3", "r7", "r8", "f1")  # what compare_args looks for; no r4/r5 (stack), no r6

CALLS = {
    "game_2010": stub(ret="void"),
    "pongPlayer_5010_g": model(_spin_from_axis),
    "BallShot_Solve": model(_solve),
    "game_2508": stub(ret=lambda ctx: ctx.rng.uniform(-3, 3)),
    "game_4B60": stub(ret="void"),
    "ballPredict_ProcessHit": _predict_model,
    "arch.vfn_15": stub(ret="void", args=("r3", "f1")),
}


def inputs(t):
    rng = t.rng
    entry = t.alloc(0x1A0, "entry")
    t.w32(entry + 0xCC, rng.choice([3, 5, 6, 7, 8, 9, 10, 11, 12, rng.randrange(-4, 20)]))
    t.w16(entry + 0xF6, rng.choice([0, 0x1000, 0x1010, 0x0FFF, rng.randrange(0, 0x10000)]))
    slot = rng.randrange(0, 4)
    t.w32(entry + 0x28, slot)
    t.wf32(entry + 0xC4, rng.choice([-9.8, -11.645, rng.uniform(-15, -5)]))
    t.floats(entry + 0x50, 4, -3, 3)
    t.floats(entry + 0x70, 4, -1, 1)
    t.floats(entry + 0x80, 4, -100, 100)
    t.floats(entry + 0xD0, 8, -10, 10)
    t.wf32(entry + 0xB0, rng.uniform(1, 30))

    inst = t.alloc(16, "inst")
    arch = t.alloc(0x40, "arch")
    holder = t.alloc(16, "holder")
    t.w32(holder, inst)
    t.w32(inst + 4, arch)
    index = rng.randrange(0, 8)
    t.w16(inst + 8, index)
    t.w32(arch, t.vtable("arch", 16))
    t.w32(BALL_SLOT, holder)

    level = t.alloc(0x20, "level")
    states = t.alloc(8, "states")
    t.w32(level + 0x1C, states)
    t.w32(LEVEL, level)

    inp = t.alloc(0x50, "input")
    for k in range(4):
        t.w32(inp + 0x38 + 4 * k, rng.choice([0, 1, 2, 3]))
    t.w32(INPUT, inp)

    state = t.alloc(0x40, "state")
    t.w32(GAME_STATE, state)

    _probe[0] = t.alloc(48, "probe", fill="zero")
    t.args(r3=entry, r4=rng.getrandbits(32), r5=1, r6=rng.getrandbits(32), r7=rng.choice([0, 1, 0x100, 0xFF]),
           f1=rng.uniform(0, 2))
