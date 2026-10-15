"""creature_inst_update_world_bound without writing the statically initialised globals
(0x82619BD0/BE0) itself: lift-check runs the game's static initializers first.
"""
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
