"""0x823B7B50: format the embedded timestamp and pass it as a log argument."""
from liftcheck.spec import *
FUNCTION = "ForceMatchTimeSyncMessage_Process"
ADDRESS = 0x823B7B50
SOURCE = "src/game/network/pong_network.cpp"
TRIALS = 200
CALLS = {"FormatTimestampForLog": stub(ret=0x45000000),
         "nop_8240E6D0": stub(ret='void', args=('r3','r4'), deref={'r3':30})}
EXTERNS = {"FormatTimestampForLog": 0x8239BF30}
def inputs(t):
    t.map(0x45000000,0x1000,'formatted',fill='zero')
    t.args(r3=t.alloc(32,'message'))
