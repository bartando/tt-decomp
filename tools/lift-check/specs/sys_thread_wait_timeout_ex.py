"""Timeout conversion, low-byte alert flag, full-word retry flag and failures."""
from liftcheck.spec import *
FUNCTION = 'sysThread_WaitTimeoutEx'
ADDRESS = 0x8242F5D0
SOURCE = 'src/xam/thread_sync.cpp'
TRIALS = 1400
state = {}


def wait(ctx):
    n = state[ctx.side]
    state[ctx.side] += 1
    ctx.ret(r3=0x101 if n < state['retries'] else state['status'])


CALLS = {
    'sysThread_MillisecondsTimeout': run(args=('r3', 'r4')),
    'NtWaitForSingleObjectEx': model(wait, args=('r3', 'r4', 'r5', 'r6'), deref={'r6': 8}),
    'sysThread_SetErrorFromStatus': stub(ret=123, args=('r3',)),
}


def inputs(t):
    state.update(orig=0, lift=0, retries=t.index % 4,
                 status=t.rng.choice([0, 0x102, 0xC0000001, 0x80000000]))
    t.args(r3=t.alloc(16, 'handle'), r4=t.rng.choice([0, 1, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF, t.u32()]),
           r5=t.rng.choice([0, 1, 2, 0x80, 0x100, 0x101]))
