"""0x821D5010: spin scaling, rotation, both mirrors and low-byte final gate."""
import struct
from liftcheck.spec import *

FUNCTION = "pongPlayer_5010_g"
ADDRESS = 0x821D5010
SOURCE = "src/game/player/player_shot_interpolation.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
EXTERNS = {
    "g_gameDataMgr": 0x8271A2E4,
    "g_pCameraSharedState": 0x8271A32C,
    "g_spinAxisRotation": 0x82606498,
    "lbl_82606750": 0x82606750,
}


def rotate(ctx):
    address = ctx.r(3)
    value = struct.unpack(">4f", ctx.read(address, 16))
    # A visible output from the called rotation; the spec checks this caller's
    # conversion, ordering and mirrors independently of the rotation's lift.
    ctx.write(address, struct.pack(">4f", value[0], -value[2], value[1], value[3]))


CALLS = {
    0x821D5998: stub(ret=lambda c: c.rng.randrange(4)),
    0x8220E1B0: stub(ret=lambda c: c.rng.uniform(-5, 5)),
    0x8223AB00: model(rotate, args=("r3", "f1"), deref={"r3": 16}),
    0x821E7CC0: stub(ret=lambda c: c.rng.choice([0, 1])),
    0x82282E70: stub(ret="void", args=("r3", "r4"), deref={"r4": 16}),
}


def inputs(t):
    axis = t.alloc(16, "axis", floats=[(0, 4)])
    t.floats(axis, 4, -3, 3)
    out = axis if t.index % 4 == 0 else t.alloc(16, "spin", floats=[(0, 4)])
    hit = t.alloc(0xD0, "hit")
    t.w16(hit + 0xC6, t.rng.getrandbits(16))
    t.w32(hit + 0x9C, t.rng.choice([0, 1, 8, 9, 10, 11]))
    t.wf32(hit + 0x68, t.rng.choice([-1, 0, 1, float("nan")]))
    manager = t.alloc(0x20, "dataManager")
    constants = t.alloc(0x40, "spinSettings")
    t.w32(manager + 0x14, constants)
    t.w32(t.sym("g_gameDataMgr"), manager)
    camera = t.alloc(0x20, "camera")
    t.w32(t.sym("g_pCameraSharedState"), camera)
    t.wf32(t.sym("g_spinAxisRotation"), t.rng.uniform(-3, 3))
    t.floats(t.sym("lbl_82606750"), 4, -1, 1)
    t.args(r3=axis, r4=out, r5=hit, r6=t.rng.choice([0, 1, 0x100, 0x101, -1]))
