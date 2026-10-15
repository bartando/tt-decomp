"""atSingletonPool_AllocEntry (0x821A91E0): append to the registry at 0x82618550, growing by 16."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from player_common import inlined
from _registry_common import heap_tls, FREE_CALLS

FUNCTION = "atSingletonPool_AllocEntry"
ADDRESS = 0x821A91E0
SOURCE = "src/rage/data/at_types.cpp"
EXTERNS = {"g_atRegistryPool": 0x82618550}

CALLS = {
    0x820DEC88: alloc(size_reg="r3"),
    0x820C29E0: stub(),                    # rage_strDuplicate
    0x821A9370: stub(),                    # delete[]
    0x820C00C0: inlined(),
    **FREE_CALLS,
}


def inputs(t):
    rng = t.rng
    pool = 0x82618550
    count = rng.choice([0, 1, 3, 16])
    cap = count if rng.random() < 0.7 else count + rng.choice([1, 5])
    data = t.alloc(16 * max(cap, 1), "data") if (count or rng.random() < 0.5) else 0
    t.w32(pool, data)
    t.w16(pool + 4, count)
    t.w16(pool + 6, cap)
    t.args(r3=rng.choice([16, t.u32()]), r13=heap_tls(t))
