"""All four argument shapes with/without bound self; zero/unknown modes do nothing."""
from liftcheck.spec import *
FUNCTION = 'sysCallback_Invoke'
ADDRESS = 0x8225FFF8
SOURCE = 'src/rage/core/rage_core_utils.cpp'
TRIALS = 1400
state = {}


def invoke(ctx):
    # Compare exactly the arguments this callback mode consumes. Other registers
    # intentionally retain MSVC-specific leftovers and are not part of its ABI.
    ctx.rec.derefs['args'] = (b''.join(ctx.r(n).to_bytes(4, 'big') for n in state['regs']), None)


CALLS = {'target': model(invoke, args=())}


def inputs(t):
    r = t.rng
    callback = t.alloc(16, 'callback')
    mode = r.choice([0, 1, 2, 3, 4, 5, 0x100, 0xFFFFFFFF])
    bound = r.choice([False, True])
    self = t.alloc(16, 'self') if bound else 0
    t.w32(callback, self)
    t.w32(callback + 4, t.fake_fn('target') if 1 <= mode <= 4 else 0)
    t.w32(callback + 8, t.u32())
    t.w32(callback + 12, mode)
    n = (1 if bound else 0) + ({1: 0, 2: 1, 3: 2, 4: 1}.get(mode, 0))
    state['regs'] = tuple(range(3, 3 + n))
    t.args(r3=callback, r4=t.u32())
