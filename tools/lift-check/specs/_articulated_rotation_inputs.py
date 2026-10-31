"""Body states and rotation vectors, including thresholds and live aliases."""
from specs._articulated_step_inputs import bodies


def vector(t, body=None):
    result = t.alloc(32, 'rotationVectorAndGuards')
    if body and t.index % 4 == 0:
        result = body + t.rng.choice((0x90, 0xA0, 0xC0, 0x130))
    values = [t.rng.uniform(-0.8, 0.8) for _ in range(4)]
    kind = t.index % 12
    if kind == 0:
        values = [0.0, -0.0, 0.0, 123.0]
    elif kind in (1, 2, 3):
        values = [(0.5e-6, 1e-6, 2e-6)[kind - 1], 0.0, -0.0, 3.0]
    elif kind == 4:
        values = [2.0**-149, -2.0**-148, 0.0, 2.0**-149]
    elif kind == 5:
        values = [float('nan'), 0.0, 0.0, 1.0]
    elif kind == 6:
        values = [float('inf'), 0.1, -0.2, -0.0]
    for lane, value in enumerate(values):
        t.wf32(result + 4 * lane, value)
    return result


def inputs(t):
    data, array = bodies(t)
    rotation = vector(t, array[0])
    t.args(r3=data, r4=rotation)
    return data, rotation
