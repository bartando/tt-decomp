"""Shared geometry/mass cases for the capsule inertia polynomial and wrappers."""

def values(t):
    special = (-0.0, 0.0, 0.001, 0.25, 1.0, 10.0, -1.0,
               float('inf'), -float('inf'), float('nan'))
    if t.index % 3 == 0:
        return tuple(t.rng.choice(special) for _ in range(3))
    if t.index % 3 == 1:
        return (t.rng.uniform(-100, 100), t.rng.uniform(0.001, 10),
                t.rng.choice((0.0, t.rng.uniform(0.001, 100))))
    radius = t.rng.uniform(-10, 10)
    return t.rng.uniform(-100, 100), radius, t.rng.uniform(-10, 10)


def wrapper_inputs(t, length_offset):
    mass, radius, length = values(t)
    shape = t.alloc(0xC0, 'shapeAndGuards') + 16
    t.wf32(shape + 0x70, radius)
    t.wf32(shape + length_offset, length)
    # Overlapping results exercise the two field loads preceding the call.
    output = (shape + t.rng.choice((0x60, 0x70, length_offset)) if t.index % 4 == 0
              else t.alloc(48, 'resultAndGuards', floats=[(16, 3)]) + 16)
    for lane in range(3):
        t.float_words.add(output + lane * 4)
    t.args(r3=output, r4=shape, f1=mass)
