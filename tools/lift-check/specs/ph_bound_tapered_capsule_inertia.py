"""0x8233AD38: hidden result r3, receiver r4, mass f1 and +70/+90 geometry."""
from liftcheck.spec import *
from specs._capsule_inertia_inputs import wrapper_inputs
FUNCTION = 'rage::phBoundTaperedCapsule::ComputeInertia'
ADDRESS = 0x8233AD38
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = {'phCapsule_ComputeInertia': run(args=('f1', 'f2', 'f3'))}


def inputs(t):
    wrapper_inputs(t, 0x90)
