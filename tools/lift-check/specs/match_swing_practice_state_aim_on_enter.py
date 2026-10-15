"""gmLogicSwingPractice::stateAim::OnEnter (slot 11, 0x82103878)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmLogicSwingPractice::stateAim::OnEnter"
ADDRESS = 0x82103878
SOURCE = "src/game/match/pong_match.cpp"

EXTERNS = {
    "game_3860": 0x821D3860,                    # the symbol map's game_3860 is 0x82483860
    "PostPageGroupMessage": 0x8225E6E0,
    "PostPageGroupMessageFmt": 0x8225E480,
    "gmPracticeTarget_PlaceRandomly": 0x82113A98,
}

# pg_E480 is variadic: lift-check doesn't model varargs, so name the registers.
# The format string lives at a different address on each side; compare 3 bytes
# ("fff" or "ff" with its terminator; what follows "ff" differs).
CALLS = {
    0x821D3860: stub(ret="void"),
    0x8225E6E0: stub(ret="void"),
    0x8225E480: stub(ret="void", args=("r3", "r4", "r6", "r7", "r8"), deref={"r5": 3}),
    0x82113A98: stub(ret="void", args=("r3", "r4")),
}
for _i in range(11):
    CALLS[f"child{_i}.vfn_9"] = stub(ret="void", args=("r3", "r4"))


def inputs(t):
    rng = t.rng
    logic = t.alloc(0xA0, "logic", ctype="gmLogicSwingPractice")
    for i in range(11):
        child = t.alloc(0x20, f"child{i}")
        t.w32(child, t.vtable(f"child{i}", 12))
        t.w32(logic + 0x28 + 4 * i, child)
    t.w32(logic + 0x54, rng.choice([-1, -2, 0, 10, 11, rng.randrange(11), rng.randrange(11)]))
    t.w8(logic + 0x59, rng.choice([0, 1, 0x20]))
    t.floats(logic + 0x70, 3, -2.0, 2.0)
    t.w32(logic + 0x98, t.alloc(0x70, "target", ctype="gmPracticeTarget"))
    state = t.alloc(0x14, "stateAim")
    t.w32(state + 0x08, logic)
    t.w8(0x8260637A, rng.choice([0, 0, 1, 0x80]))
    t.w32(0x8271A2F8, t.alloc(0x40, "gameState"))
    t.args(r3=state)
