"""game_3860 (0x821D3860): resets the ball prediction for a caller name, then
points the prediction's callback at the empty logger 0x8240E6D0 with
gameState as target (kind 4)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "game_3860"
ADDRESS = 0x821D3860
SOURCE = "src/game/match/pong_match.cpp"

CALLS = {
    0x821D7750: run(),   # exercise the actual shared Reset, including its writes
    0x82391510: stub(),
    0x8240E6D0: stub(ret="void", args=("r4", "r5")),
}


def inputs(t):
    state = t.alloc(0x40, "gameState")
    predict = t.alloc(0x2800, "ballPredict")
    count = t.rng.choice([0, 1, 3, 8, 31])
    ids = t.alloc(max(4 * count, 4), "ids")
    t.w32(predict + 0x2608, ids)
    t.w16(predict + 0x260C, count)
    for i in range(4):
        t.w32(0x8261A0C0 + 4 * i, t.rng.getrandbits(32))
    t.w32(state + 0x14, predict)
    name = t.alloc(32, "name", fill=b"gmLogicSomething::onEnterState\0\0")
    t.args(r3=state, r4=t.rng.randrange(8), r5=name)

EXTERNS = {"gdBallPredictData::Reset": 0x821D7750}
