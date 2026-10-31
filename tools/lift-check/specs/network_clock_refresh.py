"""0x82391510: virtual clock sample forwarded as f1 to the time formatter."""
from liftcheck.spec import *
FUNCTION = "pongPlayer_1510_g"
ADDRESS = 0x82391510
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 400
CALLS = {"clock.vfn_2": stub(ret=lambda ctx: ctx.rng.uniform(-10000,10000)),
         "networkFormatElapsedTime": stub(args=('r3','r4','f1'))}
def inputs(t):
    wrapper=t.alloc(32,'clock wrapper')
    clock=t.alloc(80,'clock')
    t.w32(clock,t.vtable('clock',3))
    t.w32(wrapper+12,clock)
    t.args(r3=wrapper)
