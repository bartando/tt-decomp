"""0x8228E828: compose both recovered bounds helpers and the low-byte symmetry gate."""
from liftcheck.spec import *
from specs._composite_bounds_inputs import inputs as setup, CALLS
FUNCTION = 'pongCreatureInst_E828_v12'
ADDRESS = 0x8228E828
SOURCE = 'src/game/creature/pong_creature.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'


def inputs(t):
    obj = setup(t)
    t.args(r3=obj, r4=t.pick((0, 1, 2, 0x100, 0x101, 0xff000000, 0xffffffff)))
