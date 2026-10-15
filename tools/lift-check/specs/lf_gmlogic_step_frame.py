"""gmLogic slot 3 (0x82222A78, gmLogic_StepFrame): reset state, slot 3 on each child, slot 5(-1) on the first."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmLogic_StepFrame"
ADDRESS = 0x82222A78
SOURCE = "src/rage/core/hsm.cpp"

CALLS = {
    "logic.vfn_10": stub(ret="void"),
    **{f"child{i}.vfn_3": stub(ret="void") for i in range(3)},
    "child0.vfn_5": stub(ret="void", args=("r3", "r4")),
    "child1.vfn_5": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    logic = t.alloc(0x14, "logic")
    t.w32(logic, t.vtable("logic"))
    n = rng.choice([0, 1, 3])
    arr = t.alloc(4 * max(n, 1), "children") if (n or rng.random() < 0.5) else 0
    for i in range(n):
        c = t.alloc(8, f"child{i}")
        t.w32(c, t.vtable(f"child{i}"))
        t.w32(arr + 4 * i, c)
    if arr and n == 0:
        t.w32(arr, 0)
    t.w32(logic + 4, n if arr else 0)
    t.w32(logic + 8, arr)
    t.args(r3=logic)
