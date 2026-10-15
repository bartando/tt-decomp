"""pongCreatureInst::UpdateWorldBound (slot 46): world bound sphere from the
bound's centroid and the instance matrix, manager callback +0x34C, slot 47."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::UpdateWorldBound"
ADDRESS = 0x82121530
SOURCE = "src/game/creature/pong_creature.cpp"
FTOL = 1e-6

CALLS = {
    "onBoundMoved": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    # Static initializers fill these at boot; the image holds zeros.
    # 0x8257DBF8 copies (0, 0, 0, 1) from 0x825C5850 to 0x82619BD0;
    # 0x8257DBD8 copies 0x82619C20 to 0x82619BE0, and 0x8257DB68 fills
    # 0x82619C20's x, y, z with the word at 0x825CB7F0 (0xFFFFFFFF).
    for k, v in enumerate((0, 0, 0, 0x3F800000)):
        t.w32(0x82619BD0 + 4 * k, v)
    for k, v in enumerate((0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0)):
        t.w32(0x82619BE0 + 4 * k, v)
    mgr = t.alloc(0x380, "manager")
    t.w32(mgr + 0x34C + 0x0C, t.fake_fn("onBoundMoved"))
    t.w32(0x826063B8, mgr)

    bound = t.alloc(0x90, "bound")
    t.wf32(bound + 0x08, rng.uniform(0.1, 3.0))
    t.floats(bound + 0x30, 4, -2.0, 2.0)
    arch = t.alloc(0x10, "archetype")
    t.w32(arch + 0x0C, bound)

    inst = t.alloc(0x130, "inst", ctype="pongCreatureInstLayout")
    t.w32(inst, t.vtable("inst", 60))
    t.w32(inst + 0x04, arch)
    t.floats(inst + 0x10, 16, -5.0, 5.0)
    t.floats(inst + 0x70, 5, -5.0, 5.0)
    t.w32(inst + 0x54, t.alloc(0x210, "entry") if rng.random() < 0.85 else 0)
    r = rng.random()
    if r < 0.4:
        holder = t.alloc(0x48, "typeHolder")
        t.w32(holder + 0x18, rng.choice([0, t.alloc(0x10, "type")]))
        t.w32(inst + 0x94, holder)
    else:
        t.w32(inst + 0x94, 0)
        t.w32(inst + 0x90, t.alloc(0x10, "type") if r < 0.85 else 0)
    t.args(r3=inst)
