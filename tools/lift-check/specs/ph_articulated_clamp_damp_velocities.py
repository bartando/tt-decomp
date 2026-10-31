"""0x822560F8: independent linear/angular speed limits and timestep damping.

Zero/negative/NaN limits, exact cap boundaries, ignored W in dot3 but scaled W,
nonpositive counts, repeated bodies, subnormals/nonfinites, and untouched guards.
Finite float32 results are exact; NaN encodings and signed zeros may differ.
"""
from liftcheck.spec import *
from specs._articulated_step_inputs import bodies

FUNCTION = "phArticulatedCollider_60F8"
ADDRESS = 0x822560F8
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 800
FP_CONTRACT = "off"
FTOL = 1e-99


def inputs(t):
    rng = t.rng
    data, array = bodies(t)
    linear = rng.choice((0., -1., 1., 5., 17., 1e-20, rng.uniform(0, 60)))
    angular = rng.choice((0., -1., 1., 3., 0.707, 1e-20, rng.uniform(0, 60)))
    timestep = rng.choice((0., 0.01, 1/60, 1., 10., 20., -1., rng.uniform(-10, 30)))
    kind = t.index % 13
    if kind < 3:
        # Equal-to-cap, over-cap, and zero xyz with very large W.
        for body in array:
            for offset, limit in ((0x110, linear), (0x120, angular)):
                for lane in range(4):
                    value = (abs(limit) * (kind + 1)) if lane == 0 and kind < 2 else 0.
                    t.wf32(body + offset + lane * 4, 1e10 if lane == 3 else value)
    if kind in (3, 4):
        addr = rng.choice(array) + rng.choice((0xC0, 0x110, 0x120)) + 4 * rng.randrange(4)
        t.w32(addr, rng.choice((1, 0x807FFFFF, 0x00800000, 0x7F800000, 0xFF800000, 0x7FC00000)))
    if kind == 5:
        linear = float('nan')
    if kind == 6:
        angular = float('inf')
    t.args(r3=data, f1=linear, f2=angular, f3=timestep)
