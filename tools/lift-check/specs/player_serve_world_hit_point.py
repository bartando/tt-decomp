"""0x820DD1C0: sample, conditionally rotate, then add the four-lane origin."""
import struct
from liftcheck.spec import *

FUNCTION = "game_D1C0"
ADDRESS = 0x820DD1C0
SOURCE = "src/game/player/player_serve_hit_point.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def sample(ctx):
    values = [ctx.rng.uniform(-20, 20) for _ in range(4)]
    ctx.write(ctx.r(3), struct.pack(">4f", *values))
    ctx.ret(r3=ctx.r(3))


def rotate(ctx):
    values = [ctx.rng.uniform(-20, 20) for _ in range(4)]
    ctx.write(ctx.r(3), struct.pack(">4f", *values))


CALLS = {
    0x820DD978: model(sample, args=("r3", "r4", "r5")),
    0x8223AB70: model(rotate, args=("r3", "f1")),
}


def inputs(t):
    rng = t.rng
    animation = t.alloc(0xB0, "animation", floats=[(0x40, 4)])
    t.w32(animation + 0x24, t.alloc(0x40, "clip"))
    t.w32(animation + 0x28, rng.randrange(10))
    t.floats(animation + 0x40, 4, -20, 20)
    t.wf32(animation + 0x48, rng.choice([-1.0, -0.0, 0.0, 1.0, float("nan"), rng.uniform(-20, 20)]))
    output = t.alloc(16, "output", floats=[(0, 4)])
    if t.index % 4 == 0:
        output = animation + 0x40
    t.args(r3=output, r4=animation)
