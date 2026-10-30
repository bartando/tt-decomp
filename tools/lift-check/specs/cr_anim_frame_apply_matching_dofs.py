"""Sorted animation-frame DOF intersection at 0x8224B800 (552 bytes).

Covers empty/disjoint/interleaved/identical lists, leading and trailing misses,
duplicate keys (one source consumed per match, even on rejection), all byte
types and uint16 IDs, and unsigned source counts through 0xFFFF. Both callback
paths compare order, receivers, filter type/ID/context/user data, r6=0 and f1.
Filters return noncanonical words to check low-byte truth, optionally leave the
initial 1.0 weight unchanged, or write positive/zero/negative weights. Operations
copy source payloads and record the weight so memory effects are checked too.

Limits: synthetic sorted readable frames, stable counts/keys/tables during
callbacks, modeled callbacks rather than game implementations, finite float32
weights and default rounding. Unused r8 and callback r5 are not contractual.
No ignored writes, float tolerance, match replay, or invalid-pointer testing.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::crAnimFrame_ApplyMatchingDofs"
ADDRESS = 0x8224B800
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1000
FP_CONTRACT = "off"

FILTERS = {}


def _filter(ctx):
    key = (ctx.r(4) << 16) | ctx.r(5)
    result, weight = FILTERS[key]
    if weight is not None:
        ctx.write(ctx.r(7), struct.pack(">f", weight))
    ctx.ret(r3=result)


def _operation(ctx):
    ctx.write(ctx.r(3) + 0x10, ctx.read(ctx.r(4) + 0x10, 16))
    ctx.write(ctx.r(3) + 0x20, struct.pack(">f", ctx.f(1)))


CALLS = {
    "filter": model(_filter, args=("r3", "r4", "r5", "r6", "r7"),
                    deref={"r7": 4}),
    "operation": model(_operation, args=("r3", "r4", "r6", "f1")),
}


def inputs(t):
    rng = t.rng
    pool = sorted(set([0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x10000, 0x10001,
                       0x7FFFFF, 0x800000, 0xFF0000, 0xFFFFFF]
                      + [rng.randrange(0x1000000) for _ in range(16)]))
    mode = rng.randrange(12)
    if mode == 0:
        dst_keys, src_keys = [], rng.sample(pool, rng.randrange(8))
    elif mode == 1:
        dst_keys, src_keys = rng.sample(pool, rng.randrange(8)), []
    elif mode == 2:
        dst_keys, src_keys = pool[::2], pool[1::2]
    elif mode == 3:
        dst_keys, src_keys = pool, pool
    elif mode == 4:
        dst_keys, src_keys = pool[3:-3], pool
    elif mode == 5:
        dst_keys, src_keys = pool, pool[3:-3]
    elif mode == 6:
        dst_keys = rng.choices(pool[:5], k=16)
        src_keys = rng.choices(pool[:5], k=16)
    elif mode == 7:
        dst_keys, src_keys = [pool[-1]], [pool[0]]
    elif mode == 8:
        dst_keys, src_keys = [pool[0]], [pool[-1]]
    elif mode == 9:
        dst_keys = [0xFFFFFF, 0xFFFFFF]
        src_keys = [0xFFFFFF] * rng.choice([0x7FFF, 0x8000, 0xFFFF])
    else:
        dst_keys = rng.choices(pool, k=rng.randrange(1, 25))
        src_keys = rng.choices(pool, k=rng.randrange(1, 25))

    def frame(keys, name):
        obj = t.alloc(0x10, name)
        # Large boundary lists can share one immutable-key DOF.
        repeated = len(keys) > 32
        dofs = []
        for key in sorted(keys[:1] if repeated else keys):
            dof = t.alloc(0x30, name + ".dof")
            t.w8(dof + 5, key >> 16)
            t.w16(dof + 6, key & 0xFFFF)
            dofs.append(dof)
        if repeated:
            dofs *= len(keys)
        table = t.alloc(4 * len(keys), name + ".dofs", fill="zero") if keys else 0
        if keys:
            t.put(table, b"".join(struct.pack(">I", p) for p in dofs))
        t.w32(obj + 8, table)
        t.w16(obj + 12, len(keys))
        # Capacity/flags are noise and must not control traversal.
        return obj

    dst = frame(dst_keys, "dst")
    src = frame(src_keys, "src")
    filtered = rng.choice([False, True])
    context = t.alloc(16, "context") if filtered else 0
    user = t.alloc(16, "userData") if filtered else 0
    FILTERS.clear()
    for key in set(dst_keys):
        FILTERS[key] = (rng.choice([0, 1, 2, 0xFF, 0x100, 0x101, 0x80000000]),
                        rng.choice([None, 0.0, -0.0, 1.0, -1.0, 0.125,
                                    rng.uniform(-4, 4)]))
    weight = struct.unpack(">f", struct.pack(">f", rng.uniform(-4, 4)))[0]
    t.args(r3=dst, r4=src, r5=context,
           r6=t.fake_fn("filter") if filtered else 0, r7=user,
           r8=rng.getrandbits(32), r9=t.fake_fn("operation"),
           f1=rng.choice([0.0, -0.0, 1.0, -1.0, 0.125, weight]))
