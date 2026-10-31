"""0x820CAC78: remote, saved alternate and court-derived rest transforms."""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover::CalcInitMatrix"
ADDRESS = 0x820CAC78
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000
EXTERNS = {
    "g_input_obj_ptr": 0x825EAB28,
    "g_playerModeTransitionFlag": 0x82606327,
    "g_playerModeTransform": 0x82606910,
    "g_phCapsuleShapeK": 0x825C8080,
    "lbl_82606750": 0x82606750,
}


def character(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3), 4), "big"))


def bounds(ctx):
    for reg in [5, 6]:
        ctx.write(ctx.r(reg), b"".join(struct.pack(">f", ctx.rng.uniform(-5, 5)) for _ in range(4)))


CALLS = {
    "IsMatrixIdentity": stub(ret=lambda ctx: ctx.rng.randrange(2)),
    0x8240E6D0: stub(ret="void", args=("r3", "f1", "f2", "f3")),
    "pongMatch_GetCharacterForSlot": model(character),
    "pongMatchSettings_GetCourtBounds": model(bounds, preserves=("r3",)),
}


def inputs(t):
    mover = t.alloc(0xF0, "mover", ctype="pongMover")
    out = t.alloc(64, "matrix", floats=[(0, 16)])
    settings = t.alloc(0x80, "settings")
    char = t.alloc(0x30, "character")
    stats = t.alloc(0x108, "characterStats")
    t.w32(t.sym("g_input_obj_ptr"), settings)
    t.w32(settings, char)
    t.w32(char + 0x2C, stats)
    t.wf32(stats + 0xFC, t.rng.uniform(-5, 5))
    t.w8(stats + 0x104, t.rng.choice([0, 1, 2, 0xFF]))
    slot = t.rng.randrange(2)
    t.w32(mover + 0x44, slot)
    t.w8(mover + 0x40, t.rng.choice([0, 0x10, 0xFF]))
    t.w8(settings + slot + 0x40, t.rng.choice([0, 1, 2, 0xFF]))
    t.floats(mover + 0x90, 16, -5, 5)
    t.w8(t.sym("g_playerModeTransitionFlag"), t.rng.choice([0, 1, 0xFF]))
    t.floats(t.sym("g_playerModeTransform"), 16, -5, 5)
    t.wf32(t.sym("g_phCapsuleShapeK"), t.rng.uniform(-3, 3))
    # The mirror vector's w lane matters too; include denormals in the source.
    t.floats(t.sym("lbl_82606750"), 4, -2, 2)
    if t.index % 7 == 0:
        t.w32(mover + 0x90, t.rng.choice([1, 0x80000001]))
    t.args(r3=out, r4=mover, r5=t.rng.choice([0, 1, 2, 0x100, 0x101, 0xFF]))
