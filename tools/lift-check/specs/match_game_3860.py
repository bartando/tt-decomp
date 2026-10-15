"""game_3860 (0x821D3860): resets the ball prediction for a caller name, then
points the prediction's callback at the empty logger 0x8240E6D0 with
gameState as target (kind 4)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "game_3860"
ADDRESS = 0x821D3860
SOURCE = "src/game/match/pong_match.cpp"

CALLS = {
    0x821D7750: stub(ret="void"),   # BallPredictData::Reset(data, caller)
}


def inputs(t):
    state = t.alloc(0x40, "gameState")
    predict = t.alloc(0x2800, "ballPredict")
    t.w32(state + 0x14, predict)
    name = t.alloc(32, "name", fill=b"gmLogicSomething::onEnterState\0\0")
    t.args(r3=state, r4=t.rng.randrange(8), r5=name)

EXTERNS = {"BallPredictData_Reset": 0x821D7750}
