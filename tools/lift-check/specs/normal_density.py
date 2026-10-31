"""0x821426B8: f3 sigma, rounded sqrt/exp, exact two-pi and factor-of-two terms."""
from liftcheck.spec import *
FUNCTION = 'rage::normalDensity'
ADDRESS = 0x821426B8
SOURCE = 'src/rage/math/normal_density.cpp'
TRIALS = 800
FP_CONTRACT = 'off'
CALLS = {'crt_sqrt': run(), 'crt_exp': run()}


def inputs(t):
    values = (0., -0., 1., -1., .01, -.01, 1e-20, 1e20,
              float('inf'), -float('inf'), float('nan'))
    value = t.pick(values) if t.index % 3 else t.rng.uniform(-30, 30)
    sigma = t.pick(values) if t.index % 4 else t.rng.uniform(-8, 8)
    t.args(f1=value, f2=t.rng.uniform(-1000, 1000), f3=sigma)
