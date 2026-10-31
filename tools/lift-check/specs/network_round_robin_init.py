from liftcheck.spec import *
FUNCTION = "PongNetRoundRobinCoordinator_FC20_w"
ADDRESS = 0x8220FC20
SOURCE = "src/game/network/round_robin_state.cpp"
TRIALS = 400
def _format(ctx):
    text = f'{ctx.r(6)}-{ctx.r(7)}'.encode() + b'\0'
    ctx.write(ctx.r(3),text)
    ctx.ret(r3=len(text)-1)
CALLS = {"PongNetRoundRobinCoordinator_ResetMatch": run(),
         "_snprintf": model(_format,args=('r3','r4','r5','r6','r7'),deref={'r5':6})}
def inputs(t):
    t.args(r3=t.alloc(0x3B0,'round robin'))
