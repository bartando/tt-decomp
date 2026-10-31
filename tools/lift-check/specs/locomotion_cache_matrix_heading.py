"""0x822347E8: zero/translation stores before Euler extraction; return self."""
from liftcheck.spec import *
from specs._mat33_euler_inputs import inputs as setup, CALLS as EULER_CALLS
FUNCTION = 'LocomotionStateAnim_47E8_g'
ADDRESS = 0x822347E8
SOURCE = 'src/game/creature/pong_creature.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = dict(EULER_CALLS, **{'rage::mat33ToEulerXZY': run()})


def inputs(t):
    setup(t)
    matrix = t.reg_args['r3']
    output = t.pick((matrix, matrix + 0x10, matrix + 0x20, matrix + 0x30,
                     t.alloc(64, 'headingCacheAndGuards', floats=[(16, 8)]) + 16))
    t.float_words.add(output)
    t.float_words.update(output + 0x10 + lane * 4 for lane in range(4))
    t.args(r3=output, r4=matrix)
