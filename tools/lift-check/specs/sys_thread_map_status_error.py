"""Map status first, then read suppression flag and the thread-local error slot."""
import struct
from liftcheck.spec import *
FUNCTION = 'sysThread_SetErrorFromStatus'
ADDRESS = 0x8242C330
SOURCE = 'src/xam/thread_sync.cpp'
TRIALS = 1200
EXTERNS = {'g_sda_base': 0x82600000}
state = {}


def convert(ctx):
    ctx.write(state['sda'] + 0x150, struct.pack('>I', state['suppress']))
    ctx.ret(r3=state['error'])


CALLS = {'RtlNtStatusToDosError': model(convert, args=('r3',))}


def inputs(t):
    sda = t.alloc(0x170, 'sda')
    thread = t.alloc(0x180, 'thread')
    t.w32(sda + 0x100, thread)
    t.w32(sda + 0x104, t.alloc(0x180, 'otherThread'))
    t.w32(sda + 0x150, t.u32())
    state.update(sda=sda, error=t.u32(), suppress=t.rng.choice([0, 0, 1, 0x100, t.u32()]))
    t.w32(0x82600000, sda)
    t.args(r3=t.u32(), r13=sda)
