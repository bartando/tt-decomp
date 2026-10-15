"""BallFlight_Bounce (0x822830E0): impulse bounce with friction and spin off a plane."""
import math
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "BallFlight_Bounce"
ADDRESS = 0x822830E0
SOURCE = "src/game/ball/ball_flight.cpp"
# The spin change is (n × Δv)·1.5/r with Δv nearly parallel to n, so 1-ulp
# differences in Δv (the emulated lift's scalar FPU vs the VMX unit) come out
# as up to 2^-16 rad/s in the spin; natively the lift gives the original's bits.
FTOL = 1e-4

# The lift's sqrtf (the asm's fsqrts) is a libm call for clang: park it on the
# image header and model it, out of the trace.
EXTERNS = {"sqrtf": 0x82000000}


def _sqrtf(ctx):
    ctx.ret(f1=struct.unpack(">f", struct.pack(">f", math.sqrt(ctx.f(1))))[0])


CALLS = {0x82000000: model(_sqrtf, transparent=True)}


def _vec(t, name, xyz, w):
    a = t.alloc(16, name, ctype="BallFlightVec4")
    for i, v in enumerate(list(xyz) + [w]):
        t.wf32(a + 4 * i, v)
    return a


def inputs(t):
    rng = t.rng
    if rng.random() < 0.5:
        n = (0.0, 1.0, 0.0)
    else:
        n = [rng.gauss(0, 1) for _ in range(3)]
        k = math.sqrt(sum(c * c for c in n)) or 1.0
        n = [c / k for c in n]
    into = rng.choice([-1.0, 1.0, 0.0]) * rng.uniform(0.0, 8.0)
    side = rng.choice([0.0, 0.01, 0.3, 5.0])
    vel = [-into * c + rng.uniform(-side, side) for c in n]
    spin_scale = rng.choice([0.0, 1.0, 40.0, 130.0])
    spin = [rng.uniform(-spin_scale, spin_scale) for _ in range(3)]

    normal = _vec(t, "normal", n, rng.choice([0.0, rng.uniform(-1, 1)]))
    pos = _vec(t, "pos", [rng.uniform(-2, 2) for _ in range(3)], rng.uniform(-1, 1))
    v = _vec(t, "vel", vel, rng.uniform(-1, 1))
    w = _vec(t, "spin", spin, rng.uniform(-1, 1))
    shot = t.alloc(0x1A0, "shot")
    t.args(r3=shot, r4=normal, r5=pos, r6=v, r7=w,
           f1=rng.choice([0.02, rng.uniform(0.005, 0.2)]),
           f2=rng.choice([0.0, 0.25, rng.uniform(0.0, 1.5)]),
           f3=rng.choice([0.0, 0.85, rng.uniform(0.0, 1.0)]))
