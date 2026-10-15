"""gdaiMeterLogic::RegisterSerializationFields (slot 21, 0x821E92B0): five
floats registered with rage::xmlNodeStructFloat (0x825CAF94)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gdaiMeterLogic_RegisterSerializationFields"
ADDRESS = 0x821E92B0
SOURCE = "src/game/match/pong_match.cpp"

EXTERNS = {"g_xmlNodeStructFloat": 0x825CAF94, "RegisterSerializationField": 0x821A8F58}
CALLS = {0x821A8F58: stub(ret="void")}


def inputs(t):
    t.args(r3=t.alloc(0x30, "meterLogic"))
