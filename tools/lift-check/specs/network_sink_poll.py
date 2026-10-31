"""0x82454EB8: poll/notify transitions, virtual dispatch, children and tick storage."""
from liftcheck.spec import *
FUNCTION = "msgMsgSink_4EB8_g"
ADDRESS = 0x82454EB8
SOURCE = "src/game/network/pong_network_io.cpp"
TRIALS = 800

def _status(ctx):
    ctx.write(ctx.r(3) + 0x50, ctx.rng.choice([2, 3, 4, 5, 6, 9]).to_bytes(4, 'big'))
    ctx.ret(r3=ctx.rng.choice([0, 1, 1, 2, 0xFFFFFFFF]))
def _pending(ctx): ctx.ret(r3=ctx.rng.randrange(2))
def _child(ctx): ctx.ret(r3=ctx.rng.choice([0, 1, 2, 0xFFFFFFFF, 0x80000000]))
CALLS = {"atSingleton_6F98_g": stub(args=()), "game_3FD0_h": model(_status),
         "game_9A48_h": model(_child), "session.vfn_31": model(_pending),
         "session.vfn_27": stub(ret='void'), "session.vfn_28": stub(ret='void'),
         "msgMsgSink_8B78_g": stub(ret='void'), "msgMsgSink_8B90_g": stub(ret='void')}
def inputs(t):
    sink = t.alloc(0x80, 'sink')
    session = t.alloc(16, 'session')
    t.w32(session, t.vtable('session', 32))
    t.w32(sink + 0x30, session)
    t.w32(sink + 0x50, t.rng.choice([0, 3, 3, 3, 3, 3, 3, 4, 8]))
    t.w32(sink + 0x54, t.rng.choice([0, 1, 0xFFFFFFFF]))
    t.w32(sink + 0x1C, t.alloc(8, 'header'))
    t.w32(sink + 0x20, t.alloc(16, 'notify target'))
    previous = sink + 0x24
    for i in range(t.rng.randrange(5)):
        node = t.alloc(0x20, f'child{i}')
        t.w32(previous + 4, node)
        previous = node
    t.w32(previous + 4, sink + 0x24)
    t.args(r3=sink)
