"""SinglesNetworkClient::CompareFlags (0x82329E68): unsigned compare of +4 in
this and r4: 0 / -1 / 1."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "SinglesNetworkClient::CompareFlags"
ADDRESS = 0x82329E68
SOURCE = "src/game/network/pong_network.cpp"


def inputs(t):
    a, b = t.alloc(8, "a"), t.alloc(8, "b")
    if t.rng.random() < 0.3:
        t.w32(b + 4, t.rng.randrange(1 << 32))
        t.w32(a + 4, t.rng.choice([0, 0xFFFFFFFF]))
    t.args(r3=a, r4=b)
