"""pongCreature::StepLocomotion (vtable 0x82027B08 slot 7): `this` is the
phUpdateObject base at creature + 0x10."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::StepLocomotion"
ADDRESS = 0x820C5D18
SOURCE = "src/game/creature/pong_creature.cpp"


def inputs(t):
    rng = t.rng
    creature = t.alloc(0x170, "creature")
    inst = t.alloc(0x130, "inst")
    t.w8(inst + 0x120, rng.choice([0, 1, 1, 1]))
    t.w32(creature + 0xA4, inst)

    data = t.alloc(0xE0, "charData")
    for k in range(2):
        t.w32(data + 0xD8 + 4 * k, t.alloc(0x80, f"worker{k}") if rng.random() < 0.7 else 0)
    char = t.alloc(0x20, "char")
    t.w32(char + 0x14, data)
    t.w32(creature + 0xA0, char)

    t.w8(creature + 0xE5, rng.choice([0, 1]))
    t.floats(creature + 0x110, 16, -5.0, 5.0)
    for o in (0x150, 0x151, 0x152):
        t.w8(creature + o, rng.choice([0, 1]))
    t.args(r3=creature + 0x10)
