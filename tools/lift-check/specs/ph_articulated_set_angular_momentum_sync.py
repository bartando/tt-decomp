"""0x8224F948: velocity/momentum conversion, aliasing and live joint-data reload."""
from liftcheck.spec import *
from specs._collider_velocity_inputs import inputs as setup, CALLS as BASE_CALLS
FUNCTION = 'rage::phArticulatedCollider::SetAngularVelocity'
ADDRESS = 0x8224F948
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300
FP_CONTRACT = 'off'
FTOL = 1e-99
EXTERNS = {'g_floatOne': 0x8202D108, 'g_floatZero': 0x8202D110}
CALLS = dict(BASE_CALLS)
CALLS.update({name: run() for name in ('phCollider_SetAngularVelocity',
    'phCollider_RefreshLinearVelocity', 'phCollider_RefreshAngularVelocity')})
CALLS.update({name: stub(ret='void', args=('r3', 'r4'), deref={'r3': 16, 'r4': 16})
              for name in ('phArticulatedCollider_8A30', 'phArticulatedCollider_8B10')})


def inputs(t):
    obj, _ = setup(t)
    first = t.alloc(16, 'firstJointData')
    second = t.alloc(16, 'secondJointData')
    t.w32(obj + 0x1d0, first)
    t.w32(obj + 0x30c, second)
