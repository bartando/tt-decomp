"""0x82123E78: r4 receiver, volume virtual, negative warning and 300x scale."""
import struct
from liftcheck.spec import *
FUNCTION = 'phContact_GetScaledVolume'
ADDRESS = 0x82123E78
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 500
FTOL = 1e-99
FP_CONTRACT = 'off'


def volume(ctx):
    ctx.ret(f1=struct.unpack('>f', ctx.read(ctx.r(3) + 4, 4))[0])


CALLS = {
    'volume.vfn_8': model(volume, args=('r3',)),
    'nop_8240E6D0': stub(ret='void', args=('r3',)),
}


def inputs(t):
    contact = t.alloc(0x130, 'contactPairAndGuards') + 16
    obj = t.alloc(32, 'volumeSource')
    t.w32(obj, t.vtable('volume', 9))
    t.wf32(obj + 4, t.pick((-0., 0., -1., 1., 1e38, -1e38, 2**-149,
          -2**-149, float('inf'), -float('inf'), float('nan'), t.f32(-1000, 1000))))
    t.w32(contact + 0x100, t.pick((0, obj)))
    t.args(r3=t.u32(), r4=contact)
