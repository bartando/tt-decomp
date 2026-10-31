"""0x8245BFA0: free only a non-null backing allocation, with its retail tag."""
from liftcheck.spec import *
FUNCTION='atSingleton_BFA0_g'
ADDRESS=0x8245BFA0
SOURCE='src/rage/audio/xact_buffer.cpp'
TRIALS=600
CALLS={'_locale_register':stub(ret='void',args=('r3','r4'))}
def inputs(t):
    buffer=t.alloc(0x8C,'buffer')
    data=t.alloc(32,'backing data')
    t.w32(buffer+0x78,t.rng.choice([0,data]))
    t.args(r3=buffer)
