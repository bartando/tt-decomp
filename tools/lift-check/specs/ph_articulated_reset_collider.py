"""0x8224E6D8: one reset body, correct flag/count slots and reload joint data."""
import struct
from liftcheck.spec import *
from specs.ph_collider_reset import inputs as setup, CALLS as BASE_CALLS
FUNCTION = 'rage::phArticulatedCollider::Reset'
ADDRESS = 0x8224E6D8
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300
EXTERNS = {'g_floatOne': 0x8202D108, 'g_floatZero': 0x8202D110}


def chain(ctx):
    data = ctx.r(3)
    obj, replacement = struct.unpack('>II', ctx.read(data, 8))
    ctx.write(data + 8, ctx.read(obj + 0x1d4, 8))
    ctx.write(obj + 0x1d0, struct.pack('>I', replacement))


CALLS = dict(BASE_CALLS, phCollider_Reset=run(),
    phArticulatedCollider_ResetJointChain=model(chain, args=('r3',)),
    phArticulatedCollider_5D58=stub(ret='void', args=('r3',), deref={'r3': 16}))


def inputs(t):
    setup(t)
    obj = t.reg_args['r3']
    first = t.alloc(16, 'firstJointData')
    second = t.alloc(16, 'secondJointData')
    t.w32(first, obj)
    t.w32(first + 4, second)
    t.w32(obj + 0x1d0, first)
