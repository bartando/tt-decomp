from liftcheck.spec import model
_state = {}


def get_texture(ctx):
    ctx.write(0x825EBA20, _state['fallback'].to_bytes(4, 'big'))
    ctx.ret(r3=_state['texture'])


CALLS = {
    'reference.vfn_11': model(get_texture, args=('r3',)),
    'texture.vfn_20': model(lambda ctx: ctx.ret(r3=_state['resource']), args=('r3',)),
}


def inputs(t):
    r = t.rng
    reference = t.alloc(32, 'reference')
    t.w32(reference, t.vtable('reference', slots=27))
    textures = [t.alloc(32, f'texture{i}') for i in range(3)]
    vt = t.vtable('texture', slots=26)
    for texture in textures:
        t.w32(texture, vt)
    t.w32(0x825EBA20, textures[0])
    _state['fallback'] = textures[1]
    _state['texture'] = r.choice([0, textures[2]])
    _state['resource'] = r.choice([0, t.alloc(16, 'resource')])
    t.args(r3=reference, r4=t.u32())
