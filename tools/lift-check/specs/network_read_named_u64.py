"""0x823F3EE8: read a name into the output, followed by its 64-bit identifier."""
from liftcheck.spec import *
FUNCTION = "SinglesNetworkClient::ValidateAndReadData"
ADDRESS = 0x823F3EE8
SOURCE = "src/game/network/pong_network.cpp"
TRIALS = 400
CALLS = {"datBitBuffer_ReadShortString": run(), "datBitBuffer_ReadU64": run(),
         "snBitStream_ReadString": run(), "datBitBuffer_ReadU32": run()}
def inputs(t):
    bb = t.alloc(0x28, 'stream')
    source = t.alloc(32, 'wire')
    destination = t.alloc(24, 'record')
    t.w8(source + t.rng.choice([0, 1, 7, 15]), 0)
    t.w32(bb + 4, source)
    t.w32(bb + 0x10, t.rng.choice([0, 7, 8, 127, 128, 200]))
    t.w32(bb + 0x18, 0)
    t.w32(bb + 0x1C, 0)
    t.args(r3=bb, r4=destination)
