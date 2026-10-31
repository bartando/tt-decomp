"""Selected-body responses across rooted joint trees and all three columns."""
from liftcheck.spec import *
from specs._articulated_step_inputs import bodies
from specs._articulated_force_inputs import response

CALLS = {'phSpatialTensor_Multiply': run(deref={'r4': 32})}
for i in range(8):
    for slot in (27, 28):
        CALLS[f'singleJoint{i}.vfn_{slot}'] = model(response, args=('r3', 'r4', 'r5'), deref={'r4': 32})


def tree(t):
    data, array = bodies(t)
    for body in array:
        t.w32(body, t.rng.randrange(3))
        t.float_words.discard(body)
        t.floats(body + 0x310, 48, -0.1, 0.1)
    for edge in range(1, len(array)):
        joint = t.alloc(0x240, f'singleJoint{edge - 1}')
        t.w32(joint, t.vtable(f'singleJoint{edge - 1}', 29))
        t.wf32(joint + 4, t.rng.choice((0.125, -0.25, 0.5, 1.0)))
        t.w32(data + 4 * (41 + edge), joint)
        parent = edge - 1 if t.index % 3 == 0 else t.rng.randrange(edge)
        t.w32(data + 4 * (72 + edge), parent)
    target = t.rng.randrange(len(array))
    return data, array, target


def vector(t, name):
    result = t.alloc(32, name)
    t.floats(result, 4, -10, 10)
    if t.index % 7 == 0:
        t.w32(result + t.rng.randrange(4) * 4,
              t.rng.choice((1, 0x807FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000)))
    return result


def inputs(t, angular=False):
    data, array, target = tree(t)
    force = vector(t, 'forceOrTorque')
    point = vector(t, 'point')
    if t.index % 5 == 0:
        force = array[target] + t.rng.choice((0x10, 0x30, 0x50))
        point = array[target] + 0x20
    if t.index % 11 == 0:
        point = force
    t.args(r3=data, r4=target, r5=force, r6=point)
    return data, array, target, point
