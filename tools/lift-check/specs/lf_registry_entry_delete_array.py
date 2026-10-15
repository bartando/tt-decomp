"""atRegistryEntry delete[] (0x821A9370): frees each name back to front, then the block."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from player_common import inlined
from _registry_common import heap_tls, FREE_CALLS

FUNCTION = "atRegistryEntry_DeleteArray"
ADDRESS = 0x821A9370
SOURCE = "src/rage/data/at_types.cpp"

CALLS = {0x820C00C0: inlined(), **FREE_CALLS}


def inputs(t):
    n = t.rng.choice([0, 1, 3])
    block = t.alloc(4 + 16 * max(n, 1), "block")
    t.w32(block, n)
    for i in range(n):
        t.w32(block + 4 + 16 * i, t.alloc(8, f"name{i}") if t.rng.random() < 0.7 else 0)
    t.args(r3=block + 4, r4=3, r13=heap_tls(t))
