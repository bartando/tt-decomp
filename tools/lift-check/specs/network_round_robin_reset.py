from liftcheck.spec import *
FUNCTION = "PongNetRoundRobinCoordinator_00E0_g"
ADDRESS = 0x822100E0
SOURCE = "src/game/network/round_robin_state.cpp"
TRIALS = 400
CALLS = {"PongNetRoundRobinCoordinator_ResetMatch": run()}
def inputs(t):
    t.args(r3=t.alloc(0x3B0,'round robin'))
