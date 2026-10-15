"""pongCreature::RequestTeleport: log, then teleport now or store a deferred request."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::RequestTeleport"
ADDRESS = 0x820C7CE8
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    # The no-op logger is variadic, so only its declared r3 would be compared.
    # Caller and player compare raw; the format and the suffix are string
    # literals at different addresses on the two sides, so compare their bytes
    # (47 = the format with its NUL, 11 = "(deferred)" with its NUL).
    0x8240E6D0: stub(ret="void", args=("r4", "r5"), deref={"r3": 47, "r6": 11}),
}


def inputs(t):
    rng = t.rng
    creature = t.alloc(0x170, "creature")
    t.w32(creature + 0xCC, rng.choice([0, 1, -1]))
    caller = t.alloc(0x20, "caller", fill=b"pongMover::Reset\0")
    matrix = t.alloc(0x40, "matrix")
    t.floats(matrix, 16, -5.0, 5.0)
    t.args(r3=creature, r4=caller, r5=matrix,
           r6=rng.choice([0, 1]), r7=rng.choice([0, 1]), r8=rng.choice([0, 1]))
