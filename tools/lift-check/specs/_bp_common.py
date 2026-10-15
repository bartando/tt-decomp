"""Shared input builder for the gdBallPredictData specs (not a spec itself)."""
import struct

N = 120
SAMPLE = 0x50
DATA_SIZE = 0x2800


def sample_addr(data, slot):
    return data + 0x20 + slot * SAMPLE


def fill_sample(t, a, tlo=0.0, thi=10.0):
    rng = t.rng
    t.wf32(a, rng.uniform(tlo, thi))
    t.wf32(a + 4, rng.uniform(tlo, thi))
    for k in (8, 9, 10):
        t.w8(a + k, rng.choice([0, 0, 1, 1, 2]))
    t.floats(a + 0x10, 16, -5.0, 5.0)


def predict_data(t, count=None, tail=None, sorted_times=False, name="predict"):
    """A gdBallPredictData with a consistent ring; returns (addr, tail, count)."""
    rng = t.rng
    d = t.alloc(DATA_SIZE, name, ctype="gdBallPredictData")
    if count is None:
        count = rng.choice([0, 1, 2, 3, rng.randrange(N + 1), N, N - 1])
    if tail is None:
        tail = rng.randrange(N)
    head = (tail + count) % N if rng.random() < 0.8 else rng.randrange(N)
    t.w32(d + 0x25A0, head)
    t.w32(d + 0x25A4, tail)
    t.w32(d + 0x25A8, count)
    tm = rng.uniform(0.0, 5.0)
    for i in range(N):
        a = sample_addr(d, i)
        fill_sample(t, a)
    if sorted_times:
        for i in range(count):
            a = sample_addr(d, (tail + i + 1) % N)
            tm += rng.uniform(0.005, 0.05)
            t.wf32(a, tm)
            t.wf32(a + 4, tm)
    return d, tail, count


def logical(d, tail, i):
    return sample_addr(d, (tail + i + 1) % N)

# The marker scan misses operator= (the lift would inline it otherwise).
EXTERNS = {
    "gdBallPredictSample::operator=": 0x820D6E58,
    "rage_debugLog": 0x8240E6D0,
    "pongPlayer_1510_g": 0x82391510,
    "sysCallback_Invoke": 0x8225FFF8,
    "gdReplayMgr_RecordBallSample": 0x821CD0F8,
    "g_pongMatchTiming": 0x8271A2E8,
    "g_pReplayStateData": 0x8271A2EC,
    "g_pAtSingletonPtr": 0x8271A328,
    "g_defaultData16": 0x8261A0C0,
}
