"""Real {pointer, 32-bit tag} ports at +12/+20; execute retail evaluators.

All direct/virtual/disconnected pairs, independent operands, callback side
effects, special float32 values, aliased output and random guard bytes compare
with zero tolerance. NaN/signed-zero comparison follows the checker's rules.
Only evaluator callbacks are modelled; they write the scalar out-parameter.
"""
from liftcheck.spec import model, run


def get_float(ctx):
    node = ctx.r(3)
    ctx.write(ctx.r(4), ctx.read(node + 8, 4))
    # Calls remain observable even when the arithmetic happens to commute.
    count = int.from_bytes(ctx.read(node + 12, 4), "big")
    ctx.write(node + 12, ((count + 1) & 0xffffffff).to_bytes(4, "big"))
    ctx.ret(r3=int.from_bytes(ctx.read(node + 16, 4), "big"), f1=-123.5)


CALLS = {0x82179350: run(args=("r3",), deref={"r3": 8}),
         "input.vfn_4": model(get_float, args=("r3", "r4"))}


def inputs(t):
    r = t.rng
    node = t.alloc(48, "binaryNodeAndGuards") + 4
    values = []
    tags = (1, 2, 0, 3, 0x101, 0x102, 0xffffffff, 0x80000000)
    for i, offset in enumerate((12, 20)):
        tag = tags[(t.index // (len(tags) ** i)) % len(tags)]
        payload = t.alloc(32, f"input{i}AndGuards") + 4
        value = r.uniform(-1e10, 1e10)
        t.wf32(payload, value)
        t.w32(payload + 4, t.vtable("input"))
        t.wf32(payload + 12, r.uniform(-1e10, 1e10))
        if t.index % 5 == 0:
            t.w32(payload, r.choice((0, 0x80000000, 1, 0x80000001,
                                    0x00800000, 0x7f7fffff, 0xff7fffff,
                                    0x7f800000, 0xff800000, 0x7fc12345)))
            t.w32(payload + 12, r.choice((0, 0x3f800000, 0xbf800000, 0x7f800000)))
        t.w32(node + offset, payload if tag == 1 else payload + 4 if tag == 2 else 0)
        t.w32(node + offset + 4, tag)
        values.append(payload)
    out = t.alloc(16, "outputAndGuards") + 4
    if t.index % 4 == 0:
        out = r.choice(values)  # Write after both reads, even when output aliases input.
    t.args(r3=node, r4=out)
