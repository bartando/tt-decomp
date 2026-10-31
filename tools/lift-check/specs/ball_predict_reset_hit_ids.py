"""Live hit-ID reset, classifier/recovery gates, fallback bits and cached owners."""
import struct
from liftcheck.spec import *
FUNCTION = "BallPredict_ResetHitIds"
ADDRESS = 0x82289A08
SOURCE = "src/game/ball/ball_prediction_postprocess.cpp"
TRIALS = 1000
SCRIPT = {}


def u32(c,p): return struct.unpack(">I", c.read(p,4))[0]
def w32(c,p,v): c.write(p, struct.pack(">I",v))


def build(c):
    data = SCRIPT["data"]
    c.write(SCRIPT["reset snapshot"], c.read(SCRIPT["original ids"], SCRIPT["snapshot size"]))
    c.write(SCRIPT["reset snapshot"] + SCRIPT["snapshot size"], c.read(data + 0x2610,4))
    w32(c, data + 0x2608, SCRIPT["build ids"])
    w32(c, SCRIPT["build ids"], SCRIPT["build flags"])
    w32(c, 0x8271A2F8, SCRIPT["other state"])


def recover(c):
    w32(c, SCRIPT["data"] + 0x2608, SCRIPT["recover ids"])
    w32(c, SCRIPT["recover ids"], SCRIPT["recover flags"])


def log(c):
    # The fallback retains its first IDs pointer across this call, then reloads
    # the array for bit1. Clock publication is similarly visible after logging.
    w32(c, SCRIPT["data"] + 0x2608, SCRIPT["log ids"])
    w32(c, 0x8271A2E8, SCRIPT["new clock"])


CALLS = {
    "BallPredict_BuildHitIds": model(build),
    "BallPredict_RecoverHitIds": model(recover),
    "nop_8240E6D0": model(log, args=("r3",)),
}


def inputs(t):
    rng = t.rng
    SCRIPT.clear()
    data = t.alloc(0x2800, "live prediction", ctype="gdBallPredictData")
    state = t.alloc(0x20,"game state")
    otherstate = t.alloc(0x20,"replacement state")
    t.w32(state + 0x14,data)
    t.w32(otherstate + 0x14,t.alloc(0x2800,"replacement prediction"))
    t.w32(0x8271A2F8,state)
    n = rng.choice([0,1,2,3,8,31,255])
    ids = t.alloc(max(1,n) * 4,"original ids")
    t.w32(data + 0x2608,ids)
    t.w16(data + 0x260C,n)
    buildids = t.alloc(16,"build ids")
    recoverids = t.alloc(16,"recovery ids")
    logids = t.alloc(16,"logger ids")
    clocks = [t.alloc(0x40, "clock") for _ in range(2)]
    for clock in clocks: t.wf32(clock + 0x30,rng.uniform(-10,10))
    t.w32(0x8271A2E8,clocks[0])
    size = max(1,n) * 4
    snapshot = t.alloc(size + 4,"reset snapshot")
    SCRIPT.update({"data":data,"original ids":ids,"snapshot size":size,
                   "reset snapshot":snapshot,"build ids":buildids,
                   "recover ids":recoverids,"log ids":logids,
                   "build flags":rng.choice([0,1,2,3,4,0xFFFFFFFE,0xFFFFFFFF]),
                   "recover flags":rng.choice([0,0,1,2,3,0x12345678,0xFFFFFFFF]),
                   "other state":otherstate,"new clock":clocks[1]})
    t.args(r3=rng.choice([0,1,2,-1,0x100]))
