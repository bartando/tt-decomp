"""Translate integer register arguments at the compiled-PPC32 / Xenon boundary.

Policies and call records always see Xenon registers. Snapshot before shuffling:
SysV's aligned pairs can overlap the following Xenon argument registers.
"""
from .dwarf import arg_registers

M32 = 0xFFFFFFFF


def argument_moves(sig):
    if sig is None or not any(p.type.kind == 'int' and p.type.size == 8 for p in sig.params):
        return
    orig = arg_registers(sig, limited=False)
    lift = arg_registers(sig, 'ppc32', limited=False)
    for (oreg, ty), (lreg, _) in zip(orig, lift):
        if oreg.startswith('f'):
            continue
        src = tuple(int(r[1:]) for r in lreg.split(':'))
        dst = int(oreg[1:])
        if max(*src, dst) > 10:
            from .build import BuildError
            raise BuildError(f'{sig.name}: 64-bit argument ABI translation supports register arguments only')
        yield dst, src, ty.size == 8


def to_lift(sig, gpr, gpr64):
    """Updates for a Xenon register file entering compiled code."""
    out = {}
    for dst, src, wide in argument_moves(sig):
        value = gpr64[dst] if wide else gpr[dst]
        if wide:
            out[src[0]], out[src[1]] = value >> 32, value & M32
        else:
            out[src[0]] = value
    return out


def to_xenon(sig, gpr, gpr64):
    """Updates for a compiled register file calling original code or a policy."""
    out = {}
    for dst, src, wide in argument_moves(sig):
        out[dst] = ((gpr[src[0]] << 32) | gpr[src[1]]) if wide else gpr64[src[0]]
    return out


def wide_return(sig):
    return sig is not None and sig.ret.kind == 'int' and sig.ret.size == 8
