"""Network timestamp read (0x823CEA98): s32 then a float, stream in r4."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "netTimestamp_Deserialise"
ADDRESS = 0x823CEA98
SOURCE = "src/rage/net/dat_bit_buffer.cpp"

CALLS = {
    "datBitBuffer_ReadS32": stub(ret=1, args=("r3", "r4", "r5")),
    "datBitBuffer_ReadU32": stub(ret=1, args=("r3", "r5"), out={"r4": 4}),
}


def inputs(t):
    ts = t.alloc(8, "timestamp")
    t.args(r3=ts, r4=t.alloc(0x28, "bb"))
