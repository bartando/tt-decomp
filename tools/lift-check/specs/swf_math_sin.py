"""0x823FD888: integer float tag, conversion before sine and aliased values."""
import struct
from liftcheck.spec import *
FUNCTION = 'swfMathSin'
ADDRESS = 0x823FD888
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FTOL = 1e-99


def convert(ctx):
    payload, tag = struct.unpack('>II', ctx.read(ctx.r(3), 8))
    value = struct.unpack('>f', struct.pack('>I', payload))[0] if tag == 4 else float(payload)
    ctx.ret(f1=value)


CALLS = {'swfValueToFloat': model(convert, args=('r3',), deref={'r3': 8}),
         'crt_sin': run()}


def inputs(t):
    source = t.alloc(32, 'inputAndGuards') + 16
    output = t.pick((source, source + 4, t.alloc(32, 'outputAndGuards') + 16))
    if t.index % 2:
        t.wf32(source, t.pick((-0., 0., 1e-40, t.f32(-1000, 1000))))
        t.w32(source + 4, 4)
    else:
        t.w32(source, t.rng.randrange(1000))
        t.w32(source + 4, 3)
    t.float_words.add(output)
    t.args(r3=t.u32(), r4=t.u32(), r5=source, r6=output)
