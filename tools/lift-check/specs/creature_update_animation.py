"""pongCreature::UpdateAnimation: player-state update, swing hand-off, look-at.

The predicates 0x820CD550/598/5F0/660 run as the originals: the original keeps
the state pointer in r4 across the first two (they are leaves that don't touch
r4), which only holds when they really run.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::UpdateAnimation"
ADDRESS = 0x820C69A0
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    0x820CD550: run(),
    0x820CD598: run(),
    0x820CD5F0: run(),
    0x820CD660: run(),
    # Writes the swing target into outTarget and returns outTarget.
    0x820CD7B0: stub(ret=lambda ctx: ctx.r(3), out={"r3": 16}),
    0x820CB208: stub(ret="void", deref={"r4": 16}),
}


def inputs(t):
    rng = t.rng
    creature = t.alloc(0x170, "creature")
    t.w32(creature + 0xAC, t.alloc(0x20, "skeleton"))
    t.w32(creature + 0xA8, t.alloc(0x40, "swingState") if rng.random() < 0.8 else 0)
    t.w32(creature + 0xCC, rng.choice([0, 1, -1]))
    t.w8(creature + 0xF0, rng.choice([0, 1, 1]))
    t.w32(creature + 0xF8, t.alloc(0x40, "lookAt"))

    if rng.random() < 0.85:
        state = t.alloc(0xC0, "state")
        t.w8(state + 0x14, rng.choice([0, 1]))
        obj8c = t.alloc(0x10, "state.obj8C")
        t.w32(obj8c, t.vtable("obj8C", 8))
        t.w32(state + 0x8C, obj8c)
        for off, size in ((0x7C, 0x40), (0x80, 0xB0), (0x88, 0x1A0)):
            if rng.random() < 0.75:
                p = t.alloc(size, f"state+{off:X}")
                t.w32(state + off, p)
                if off == 0x7C:
                    t.floats(p + 0x1C, 1, 0.0, 2.0)
                    t.floats(p + 0x30, 1, 0.0, 2.0)
                elif off == 0x80:
                    t.w8(p + 0x2C, rng.choice([0, 0, 1]))
                    t.floats(p + 0xAC, 1, -1.0, 2.0)
                else:
                    t.w16(p + 0x5A, rng.getrandbits(16))
                    t.floats(p + 0x19C, 1, -1.0, 1.0)
            else:
                t.w32(state + off, 0)
    else:
        state = 0
    t.w32(creature + 0xBC, state)

    replay = t.alloc(0x68D00, "replay", fill="zero")
    t.w32(replay + 0x68CF0, rng.choice([0, 1]))
    t.w32(0x8271A2EC, replay)
    t.w32(0x825C9F3C + 4, rng.choice([0, 0, 1]))
    t.w8(0x82606325, rng.choice([0, 0, 1]))
    t.args(r3=creature)
