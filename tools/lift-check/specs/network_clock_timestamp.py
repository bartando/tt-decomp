"""0x82391480: cache hit/miss, signed whole seconds, four-byte clock slots."""
from liftcheck.spec import *
FUNCTION = "networkClockTimestamp"
ADDRESS = 0x82391480
SOURCE = "src/game/network/network_timestamp.cpp"
TRIALS = 600
CALLS = {"networkFormatElapsedTime": stub(args=('r3','r4','f1'))}
def inputs(t):
    import struct
    clock=t.alloc(64,'clock pointer array')
    slot=t.rng.randrange(6)
    timestamp=t.alloc(80,'cached timestamp')
    whole=t.rng.choice([-100,0,1,60,0x7FFFFFFF,-0x80000000])
    fraction=t.rng.choice([-1.5,-0.0,0.0,0.125,0.999,1.5])
    f32=lambda v: struct.unpack('>f',struct.pack('>f',v))[0]
    current=f32(fraction+f32(whole))
    t.w32(clock+(slot+3)*4,timestamp)
    t.w32(timestamp+4,whole)
    t.wf32(timestamp+8,fraction)
    t.wf32(timestamp+12,t.rng.choice([current,current,0.5,-999]))
    t.args(r3=clock,r4=slot)
