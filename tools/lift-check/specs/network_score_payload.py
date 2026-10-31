"""0x82390608: every score field, call order and ignored read-success flags."""
from liftcheck.spec import *
FUNCTION = "netScore_Deserialise"
ADDRESS = 0x82390608
SOURCE = "src/game/network/score_payload.cpp"
TRIALS = 400
CALLS = {"datBitBuffer_ReadU8": stub(out={"r4": 1}),
         "datBitBuffer_ReadU32": stub(out={"r4": 4}),
         "datBitBuffer_ReadS32": stub(out={"r4": 4}),
         "datBitBuffer_ReadS8": stub(out={"r4": 1})}
def inputs(t):
    score = t.alloc(32, "score")
    client = t.alloc(0x28, "stream")
    t.args(r3=score, r4=client)
