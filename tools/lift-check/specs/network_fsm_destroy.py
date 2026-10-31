"""0x822227A8: base-vtable transitions and release of the optional state buffer."""
from liftcheck.spec import *
FUNCTION = "fsmMachine_Destructor_27A8"
ADDRESS = 0x822227A8
SOURCE = "src/rage/core/fsmMachine.cpp"
TRIALS = 400
_machine = [0]
def _free(ctx):
    ctx.rec.derefs['machine during release'] = (ctx.read(_machine[0], 12), None)
    ctx.ret()
CALLS = {"rage_free": model(_free)}
def inputs(t):
    machine = t.alloc(12,'machine')
    storage = t.alloc(32,'states')
    t.w32(machine + 8,t.rng.choice([0,storage]))
    _machine[0] = machine
    t.args(r3=machine)
