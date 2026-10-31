"""0x820C9F40: rest transform, optional teleport and complete motion reset."""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover::Reset"
ADDRESS = 0x820C9F40
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000
EXTERNS = {"g_sceneRenderObj": 0x82606430}


def matrix(ctx):
    ctx.write(ctx.r(3), b"".join(struct.pack(">f", ctx.rng.uniform(-5, 5)) for _ in range(16)))
    # CalcInitMatrix may update the mover; Reset must read its current index.
    ctx.write(ctx.r(4) + 0x44, struct.pack(">I", ctx.rng.randrange(2)))
    ctx.ret(r3=ctx.r(3))


CALLS = {
    "pongMover::CalcInitMatrix": model(matrix),
    "pongCreature::RequestTeleport": stub(ret="void", deref={"r5": 64}),
    0x8240E6D0: stub(ret="void", args=("r3",)),
}


def inputs(t):
    mover = t.alloc(0xF0, "mover", ctype="pongMover")
    creature = t.alloc(16, "creature")
    table = t.alloc(0x100, "players")
    t.w32(t.sym("g_sceneRenderObj"), table)
    for i in range(2):
        t.w32(table + (i + 0x21) * 4, i)
        t.w32(table + (i + 0x1D) * 4, t.rng.choice([0, 1]))
    t.w32(mover + 0x44, t.rng.randrange(2))
    t.w32(mover + 0x70, t.rng.choice([0, creature]))
    t.args(r3=mover, r4=t.index % 2)
