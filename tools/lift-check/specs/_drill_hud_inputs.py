"""Page-group lock/lookup policies shared by the training HUD setter specs."""
import struct
import zlib
from liftcheck.spec import *

state = {}


def _lookup(ctx):
    key = bytearray()
    while (c := ctx.read(ctx.r(4) + len(key), 1)) != b'\0':
        key.extend(c)
    ctx.rec.gpr[1] = zlib.crc32(key)
    ctx.ret(r3=state['entry'])


def _group(ctx):
    # The arrow-direction setter reads +0xB8 after this callback, not before it.
    ctx.write(ctx.r(3) + 0xB8, struct.pack('>I', state['direction']))
    ctx.ret(r3=state['group'])


CALLS = {
    'hudFlashBase_IsNetworkDirty': stub(ret=lambda c: state['acquired'], args=('r3',)),
    'hudFlashBase_GetPageGroup': model(_group, args=('r3',)),
    'SinglesNetworkClient_BindEntry': model(_lookup, args=('r3', 'r4')),
    'hudFlashBase_PublishPageGroup': stub(ret='void', args=('r3',)),
}


def inputs(t):
    r = t.rng
    hud = t.alloc(0xD0, 'hud')
    state.update(entry=t.alloc(16, 'entryAndGuard') if t.index % 3 else 0,
                 group=t.alloc(0xC0, 'group'), direction=t.u32(),
                 acquired=r.choice([0, 1, 2, 0x80, 0x100, 0x101]))
    t.args(r3=hud, r4=r.choice([0, 1, 2, 0x80, 0x100, -1, t.u32()]))
