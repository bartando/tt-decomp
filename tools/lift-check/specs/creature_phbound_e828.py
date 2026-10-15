"""pongCreatureInst_E828_v12 (0x8228E828, a rage::phBound function): 0x8228E888,
radius = 0x8228ECB0(bound, parts matrices, centroid), 0x8228F3E0 when flags."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst_E828_v12"
ADDRESS = 0x8228E828
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    0x8228E888: stub(ret="void"),
    0x8228ECB0: stub(ret=lambda ctx: ctx.rng.uniform(0.0, 5.0), args=("r3", "r4", "r5")),
    0x8228F3E0: stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    bound = t.alloc(0x90, "bound", ctype="phBoundView")
    t.w32(bound + 0x78, rng.getrandbits(32))
    t.args(r3=bound, r4=rng.choice([0, 1, 0x100, rng.getrandbits(32)]))
