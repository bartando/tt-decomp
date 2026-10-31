"""0x8225FFF8: free/bound dispatch, all four argument modes, empty/unknown kinds."""
from liftcheck.spec import *

FUNCTION = "sysCallback_Invoke"
ADDRESS = 0x8225FFF8
SOURCE = "src/rage/core/rage_core_utils.cpp"
TRIALS = 1000


def invoked(argc):
    def call(ctx):
        if argc and (dest := ctx.r(argc + 2)):
            ctx.write(dest, ctx.rng.getrandbits(32).to_bytes(4, "big"))
    return model(call, args=tuple(f"r{3 + i}" for i in range(argc)))


CALLS = {}
for kind, argc in ((1, 0), (2, 1), (3, 2), (4, 1)):
    CALLS[f"free{kind}"] = invoked(argc)
    CALLS[f"bound{kind}"] = invoked(argc + 1)


def inputs(t):
    rng = t.rng
    callback = t.alloc(16, "callback", ctype="SystemCallback")
    kind = t.index % 9
    if kind == 5:
        kind = 0x100
    elif kind == 6:
        kind = 0xFFFFFFFF
    target = t.alloc(16, "target") if rng.choice([False, True]) else 0
    stored = t.alloc(16, "storedArgument")
    runtime = t.alloc(16, "runtimeArgument")
    t.w32(callback, target)
    t.w32(callback + 4, t.fake_fn(f"{'bound' if target else 'free'}{kind}"))
    t.w32(callback + 8, rng.choice([0, stored]))
    t.w32(callback + 0x0C, kind)
    t.args(r3=callback, r4=rng.choice([0, runtime]))
