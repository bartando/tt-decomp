"""BallFlight_Acceleration (0x822832D0): spin, drag and scaled gravity on the ball."""
import math

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "BallFlight_Acceleration"
ADDRESS = 0x822832D0
SOURCE = "src/game/ball/ball_flight.cpp"
# vmsum3fp128 sums in one rounding; the lift's dot product rounds per term.
FTOL = 1e-5



CALLS = {
    "crt_tan": stub(ret=math.tan(math.pi / 3)),
    "crt_sqrt": stub(ret=lambda ctx: math.sqrt(max(ctx.f(1), 0.0))),
    "arch.vfn_12": stub(ret=lambda ctx: ctx.rng.choice([1.0, 1.188, 0.0, ctx.rng.uniform(0.5, 1.5)])),
}


def inputs(t):
    rng = t.rng
    out = t.alloc(16, "out", fill="zero", ctype="BallFlightVec4")
    shot = t.alloc(0x1A0, "shot")
    t.w32(shot + 0xCC, rng.choice([3, 5, 8, 9, 10, rng.randrange(0, 16)]))
    vel = t.alloc(16, "vel")
    spin = t.alloc(16, "spin")
    scale = rng.choice([0.0, 1e-4, 1.0, 20.0])
    for i in range(3):
        t.wf32(vel + 4 * i, rng.uniform(-1, 1) * scale)
        t.wf32(spin + 4 * i, rng.uniform(-130, 130))
    t.wf32(vel + 12, rng.uniform(-1, 1))
    t.wf32(spin + 12, rng.uniform(-1, 1))
    if rng.random() < 0.3:  # mostly sideways: the spin's horizontal part is dropped
        t.wf32(vel + 0, 10.0)
        t.wf32(vel + 8, rng.uniform(-5.0, 5.0))

    inst = t.alloc(16, "inst")
    arch = t.alloc(0x40, "arch")
    holder = t.alloc(16, "holder")
    t.w32(holder, inst)
    t.w32(inst + 4, arch)
    t.w32(arch, t.vtable("arch", 16))
    t.w32(0x8271A2F4, holder)  # g_ppBallInst
    t.args(r3=out, r4=shot, r5=vel, r6=spin)
