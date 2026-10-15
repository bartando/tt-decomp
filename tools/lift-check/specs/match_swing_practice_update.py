"""gmLogicSwingPractice::Update (slot 11, 0x82102A90): spins the target, updates
the ball robot, passes the frame time to the active child's slot 6."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmLogicSwingPractice::Update"
ADDRESS = 0x82102A90
SOURCE = "src/game/match/pong_match.cpp"

EXTERNS = {"gmBallRobot_Update": 0x82112508}

CALLS = {
    0x821129D0: stub(args=("f1", "f2", "f3")),   # WrapValueInRange(value, -pi, pi)
    0x82112508: stub(ret="void"),                # gmBallRobot update
}
for _i in range(11):
    CALLS[f"child{_i}.vfn_6"] = stub(ret="void", args=("r3", "f1"))


def inputs(t):
    rng = t.rng
    logic = t.alloc(0xA0, "logic", ctype="gmLogicSwingPractice")
    for i in range(11):
        child = t.alloc(0x20, f"child{i}")
        t.w32(child, t.vtable(f"child{i}"))
        t.w32(logic + 0x28 + 4 * i, child)
    t.w32(logic + 0x54, rng.choice([-1, -2, 0, 5, 10, 11, 12, rng.randrange(11), 0x80000000]))
    t.w8(logic + 0x58, rng.choice([0, 1, 0x80]))
    if rng.random() < 0.8:
        target = t.alloc(0x70, "target", ctype="gmPracticeTarget")
        t.w8(target + 0x64, rng.choice([0, 0, 1]))
        t.wf32(target + 0x60, rng.uniform(-3.2, 3.2))
        t.w32(logic + 0x98, target)
    else:
        t.w32(logic + 0x98, 0)
    t.w32(logic + 0x94, t.alloc(0x40, "ballRobot") if rng.random() < 0.7 else 0)
    t.wf32(0x825CAEB8 + 8, rng.choice([1 / 60, 1 / 30, rng.uniform(0, 0.1)]))
    t.args(r3=logic)
