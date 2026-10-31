"""0x823FF2F0: convert the tagged key through A768, match complete local names,
copy the two value words in order, or delegate the original tagged key to slot
10. Covers empty/prefix/case/long names, negative/zero counts, duplicate names,
null values, and output aliasing the value array (including a one-word overlap).
The real key conversion runs on both sides; only the inner object is modelled.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfACTIONFUNC::GetMember"
ADDRESS = 0x823FF2F0
SOURCE = "src/rage/swf.cpp"
TRIALS = 1200


def inner(c):
    c.write(c.r(5), c.read(c.r(3) + 8, 8))
    c.ret(r3=int.from_bytes(c.read(c.r(3) + 4, 4), 'big'))


CALLS = {
    "util_A768_1": run(),
    "inner.vfn_10": model(inner, args=("r3", "r4", "r5"), deref={"r4": 8}),
}


def inputs(t):
    r = t.rng
    obj = t.alloc(0x1CB0, "action")
    inner_obj = t.alloc(16, "inner")
    t.w32(inner_obj, t.vtable("inner", 11))
    t.w32(inner_obj + 4, r.choice([0, 1, 0x100, 0xFFFFFFFF, t.u32()]))
    t.w32(obj + 0x1CA4, inner_obj)
    n = r.choice([-3, 0, 1, 2, 5, 8])
    t.w32(obj + 0x84, n)
    names = [b'', b'alpha', b'alphabet', b'alph', b'Alpha', b'x', b'x' * 127, b'\xffx']
    locals_ = [r.choice(names) for _ in range(max(n, 0))]
    for i, name in enumerate(locals_):
        t.put(obj + 0x88 + 128 * i, name + b'\0')
    text = r.choice(names + locals_)
    key = t.alloc(8, "taggedKey")
    t.w32(key, t.alloc(len(text) + 1, "keyText", fill=text + b'\0'))
    t.w32(key + 4, 1)
    values = t.alloc(16 + 8 * max(n, 1), "localValuesAndGuards") + 8
    t.w32(obj + 0x1CA0, values)
    out = r.choice([t.alloc(8, "out"), values, values + 4])
    t.args(r3=obj, r4=key, r5=out)
