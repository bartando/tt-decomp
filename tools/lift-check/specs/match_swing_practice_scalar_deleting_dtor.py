"""gmLogicSwingPractice::ScalarDeletingDtor (slot 0, 0x82101F80): destructor body 0x82101FD0,
then rage_free when bit 0 of the flags is set; returns this."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmLogicSwingPractice::ScalarDeletingDtor"
ADDRESS = 0x82101F80
SOURCE = "src/game/match/pong_match.cpp"

EXTERNS = {"gmLogicSwingPractice_Destruct": 0x82101FD0}

CALLS = {
    0x82101FD0: stub(ret="void"),
    0x820C00C0: stub(ret="void"),   # rage_free
}


def inputs(t):
    obj = t.alloc(0xA0, "obj")
    t.args(r3=obj, r4=t.rng.choice([0, 1, 2, 3, 0xFFFFFFFE, t.u32()]))
