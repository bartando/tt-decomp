from liftcheck.spec import *

# Finite float bits, plus both boolean values. The read result is intentionally
# random: message handlers ignore it, as does the original.
def _read_word(ctx):
    ctx.write(ctx.r(4), ctx.rng.choice([0, 1, 0x3F800000, 0xC0100000]).to_bytes(4, 'big'))
    ctx.ret(r3=ctx.rng.randrange(2))

EXTERNS = {"netStream_ReadS16": 0x820D7970}

CALLS = {0x82238DF8: model(_read_word, args=('r3', 'r4', 'r5')),
         0x82260AF0: stub(out={'r4': 96}, args=('r3', 'r4', 'r5')),
         0x82390608: stub(ret='void', args=('r3', 'r4')),
         0x820D7970: stub(out={'r4': 2}, args=('r3', 'r4'))}

def inputs(t):
    message = t.alloc(160, 'message')
    client = t.alloc(0x28, 'stream')
    t.args(r3=message, r4=client)
