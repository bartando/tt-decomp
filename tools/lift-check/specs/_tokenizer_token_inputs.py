"""Token read virtual with position changes, zero result and match/mismatch cases."""
import struct
from liftcheck.spec import *


def get_token(ctx):
    obj, out, size = ctx.r(3), ctx.r(4), ctx.r(5)
    source, length = struct.unpack('>Ii', ctx.read(obj + 0x240, 8))
    token = bytearray()
    for i in range(120):
        byte = ctx.read(source + i, 1)
        token += byte
        if byte == b'\0': break
    if length:
        ctx.write(out, token[:size])
    ctx.write(obj + 0x10, ctx.read(obj + 0x248, 4))
    ctx.ret(r3=length)


CALLS = {
    'tokenReader.vfn_1': model(get_token, args=('r3', 'r4', 'r5')),
    'fiTokenizer_PushBackToken': run(),
    'strchr': run(),
    '_stricmp': run(),
}
EXTERNS = {'strchr': 0x824321B0, '_stricmp': 0x82433A40}


def inputs(t):
    obj = t.alloc(0x300, 'tokenizerAndGuards') + 16
    t.w32(obj, t.vtable('tokenReader', 2))
    value = t.pick((b'', b'alpha', b'a b', b'a\tb', b'"ab"', b'AbCd', b'x'))
    source = t.alloc(128, 'tokenPayload')
    t.put(source, value + b'\0')
    expected = t.alloc(128, 'expectedToken')
    target = t.pick((value, value.upper(), b'', b'different'))
    t.put(expected, target + b'\0')
    t.w32(obj + 0x240, source)
    t.w32(obj + 0x244, t.pick((0, len(value), len(value))))
    t.args(r3=obj, r4=expected, r5=t.pick((0, 1)))
