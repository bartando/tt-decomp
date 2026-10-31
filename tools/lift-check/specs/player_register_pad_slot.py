"""0x821C9C60: forward the camera-side byte into pad configuration."""
from liftcheck.spec import *

FUNCTION = "pongPlayer_9C60_g"
ADDRESS = 0x821C9C60
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 500
CALLS = {
    0x821E7CC0: stub(ret=lambda c: c.rng.randrange(2)),
    0x821E05A8: stub(ret="void", args=("r3", "r4", "r5")),
}
EXTERNS = {"g_pPlayerRecords": 0x8271A31C, "g_pCameraSharedState": 0x8271A32C}


def inputs(t):
    data = t.alloc(0x50, "slotData")
    records = t.alloc(4 * 808 + 12, "records")
    camera = t.alloc(16, "camera")
    t.w32(0x8271A31C, records)
    t.w32(0x8271A32C, camera)
    index = t.index % 2
    t.w32(records + (index + 1) * 4, t.rng.choice([-2, -1, 0, 1, 2, 3, 4]))
    t.args(r3=data, r4=index, r5=t.rng.getrandbits(32))
