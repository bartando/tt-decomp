from liftcheck.spec import *
FUNCTION = "PongNetRoundRobinCoordinator_ResetMatch"
ADDRESS = 0x822110F8
SOURCE = "src/game/network/round_robin_state.cpp"
TRIALS = 400
def inputs(t):
    t.args(r3=t.alloc(32,'match'))
