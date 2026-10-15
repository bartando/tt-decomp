"""gmLogicSwingPractice::OnMessage (slot 18, 0x82102BF0)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmLogicSwingPractice::OnMessage"
ADDRESS = 0x82102BF0
SOURCE = "src/game/match/pong_match.cpp"

CALLS = {"logic.vfn_3": stub(ret="void", args=("r3",))}
for _i in range(8):
    CALLS[f"state{_i}.vfn_16"] = stub(ret="void", args=("r3", "r4"))
for _i in range(11):
    CALLS[f"child{_i}.vfn_8"] = stub(ret="void", args=("r3", "r4"))


def inputs(t):
    rng = t.rng
    logic = t.alloc(0xA0, "logic", ctype="gmLogicSwingPractice")
    t.w32(logic, t.vtable("logic", 20))
    states = t.alloc(4 * 8, "states")
    for i in range(8):
        if rng.random() < 0.8:
            s = t.alloc(0x20, f"state{i}")
            t.w32(s, t.vtable(f"state{i}", 20))
            t.w32(states + 4 * i, s)
        else:
            t.w32(states + 4 * i, 0)
    t.w32(logic + 0x04, 8)
    t.w32(logic + 0x08, states)
    t.w32(logic + 0x0C, rng.choice([-1, rng.randrange(8), rng.randrange(8)]))
    t.w32(logic + 0x10, rng.choice([-1, -1, rng.randrange(8)]))
    for i in range(11):
        child = t.alloc(0x20, f"child{i}")
        t.w32(child, t.vtable(f"child{i}", 20))
        t.w32(logic + 0x28 + 4 * i, child)
    t.w32(logic + 0x54, rng.choice([-1, -2, 0, 10, 11, rng.randrange(11), rng.randrange(11)]))
    msg = t.alloc(0x10, "msg")
    t.w16(msg, rng.choice([0x500C, 0x500D, 0x500C, 0x500D, 0x500E, 0x100C, rng.randrange(0x10000)]))
    t.args(r3=logic, r4=msg)
