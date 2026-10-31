"""0x820E6E90: clamp heading near either rectangle axis with exact sector gates."""
from liftcheck.spec import *
from specs._locomotion_heading_inputs import inputs, CALLS
FUNCTION = 'LocomotionStateAnim_ClampHeading'
ADDRESS = 0x820E6E90
SOURCE = 'src/anim/locomotion_heading.cpp'
TRIALS = 1000
FP_CONTRACT = 'off'
