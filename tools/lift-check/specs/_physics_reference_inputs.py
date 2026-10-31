"""Reference wraparound, instrumentation bypass and exact scalar virtual calls."""
from liftcheck.spec import *
CALLS = {'reference.vfn_0': stub(ret='void', args=('r3', 'r4'), deref={'r3': 0x68}),
         'reference.vfn_3': stub(ret='void', args=('r3',), deref={'r3': 0x68}),
         'ph_CEE0': run()}


def reference(t, name):
    obj = t.alloc(0x90, name) + 16
    t.w32(obj, t.vtable('reference', 4))
    t.w16(obj + 0x1a, t.pick((0, 1, 2, 3, 0x7fff, 0xffff)))
    t.w16(obj + 0x60, t.pick((0, 1, 2, 3, 0x7fff, 0xffff)))
    return obj


def inputs(t):
    obj = reference(t, 'referenceObjectAndGuards')
    enabled = t.pick((0, 1, 2, 0x80, 0xff))
    t.w8(0x826064E1, enabled)
    if not enabled and t.index % 2 == 0:
        obj = 0
    t.args(r3=obj, r4=t.pick((0, 1, 2, 0x100, 0x101, -1, 0xff000000)))


def swap_inputs(t):
    owner = t.alloc(48, 'archetypeAndGuards') + 16
    old = reference(t, 'oldBoundAndGuards')
    new = reference(t, 'newBoundAndGuards')
    old = t.pick((0, old, new))
    new = t.pick((0, new, old))
    t.w32(owner + 0x0c, old)
    t.w8(0x826064E1, t.pick((0, 1, 2, 0x80, 0xff)))
    t.args(r3=owner, r4=new)
