"""0x82256968: translate all four lanes; thresholded angular basis integration.

Run original CRT/rotation/composition dependencies, each lifted helper separately
checked. Exact finite float32 results; NaN encoding and signed zero may differ.
VMX reciprocal follows the harness estimate, not measured console accuracy.
"""
from liftcheck.spec import *
from specs._articulated_step_inputs import bodies
FUNCTION = 'rage::ph_IntegrateJointPositions'
ADDRESS = 0x82256968
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 600
FP_CONTRACT = 'off'
FTOL = 1e-99
CALLS = {'crt_sqrt': run(), 'crt_cos': run(), 'crt_sin': run(), 'phArticulatedCollider_BuildRotation': run(),
         'rage::mat33ComposeInPlace': run()}


def inputs(t):
    data, array = bodies(t)
    kind = t.index % 9
    if kind < 4:
        speed = (0., 0.0001, 0.001, 0.0011)[kind]
        for body in array:
            for lane in range(4):
                t.wf32(body + 0x120 + lane * 4, speed if lane == 0 else 0.)
    if kind == 4:
        t.w32(t.rng.choice(array) + 0x120, 0x7FC00000)
    if kind == 5:
        t.w32(t.rng.choice(array) + t.rng.choice((0xC0, 0x110)) + 4 * t.rng.randrange(4),
              t.rng.choice((1, 0x807FFFFF, 0x7F800000, 0x7FC00000)))
    timestep = t.rng.choice((0., -0.01, 1/60, 1/30, 1., t.rng.uniform(-1, 1)))
    t.args(r3=data, f1=timestep)
