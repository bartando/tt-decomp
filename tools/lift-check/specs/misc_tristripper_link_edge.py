"""TriStripper::LinkEdge: finds the later triangle sharing an edge (reversed) and
records the pair on both sides."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "TriStripper::LinkEdge"
ADDRESS = 0x821354D0
SOURCE = "src/game/misc/cm_operators.cpp"


def mesh(t, n):
    """Triangles over a small vertex pool so edges get shared, in both windings."""
    rng = t.rng
    nv = rng.choice([4, 6, 10])
    idx = t.alloc(6 * n, "indices")
    for k in range(n):
        a, b, c = rng.sample(range(nv), 3)
        for j, v in enumerate((a, b, c)):
            t.w16(idx + 6 * k + 2 * j, v)
    return idx


def inputs(t):
    rng = t.rng
    n = rng.choice([2, 3, 6, 12, 20])
    s = t.alloc(0x10, "stripper")
    nb = t.alloc(0x18 * n, "neighbors")
    flags = t.alloc(4 * n, "flags", fill="zero")
    for k in range(n):
        t.w32(flags + 4 * k, rng.choice([0, 0, 1, 2, 4, 3, 5, 6, 7, 7]))
    t.w32(s + 0x00, n)
    s_idx = [mesh(t, n)]
    t.w32(s + 0x04, s_idx[0])
    t.w32(s + 0x08, nb)
    t.w32(s + 0x0C, flags)
    tri, edge = rng.randrange(n - 1), rng.randrange(3)
    if rng.random() < 0.7:     # plant the reversed edge in a later triangle
        base = s_idx[0]
        frm = rng.randrange(10)
        to = (frm + 1 + rng.randrange(9)) % 10
        t.w16(base + 6 * tri + 2 * edge, frm)
        t.w16(base + 6 * tri + 2 * ((edge + 1) % 3), to)
        other, oe = rng.randrange(tri + 1, n), rng.randrange(3)
        t.w16(base + 6 * other + 2 * oe, to)
        t.w16(base + 6 * other + 2 * ((oe + 1) % 3), frm)
    t.args(r3=s, r4=tri, r5=edge)
