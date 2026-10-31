"""0x8245BF40: clear 140 bytes and preserve the internal +0x6C pointer."""
from liftcheck.spec import *
FUNCTION='msgMsgSink_BF40_g'
ADDRESS=0x8245BF40
SOURCE='src/rage/audio/xact_buffer.cpp'
TRIALS=600
def inputs(t): t.args(r3=t.alloc(0xA0,'buffer and guard'))
