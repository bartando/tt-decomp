"""pongCreature::DestroyThunk (0x820C8618, vtable 0x82027B08 slot 2):
`addi r3, r3, -0x10; b 0x820C5398`, r4 passed through."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::DestroyThunk"
ADDRESS = 0x820C8618
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    0x820C5398: stub(args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    base = t.alloc(0x100, "creature")
    t.args(r3=base + 0x10, r4=rng.choice([0, 1, rng.getrandbits(32)]))
