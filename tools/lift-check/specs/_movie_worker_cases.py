from liftcheck.spec import *

def ring_inputs(t):
    ring = t.alloc(128, "ring")
    cases = [(0, 0), (1, 0), (8, 6), (8, 7), (8, 8),
             (8, 0xFFFFFFFF), (0xFFFFFFFF, 0xFFFFFFFE), (0xFFFFFFFF, 0xFFFFFFFF)]
    capacity, index = cases[t.index % len(cases)]
    t.w32(ring + 0x34, capacity)
    t.w32(ring + 0x38, index)
    t.w32(ring + 0x3C, index)
    t.w32(ring + 0x44, [0, 1, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000,
                       t.rng.getrandbits(32)][t.index % 6])
    t.args(r3=ring)

def worker_call(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 4, ctx.rng.getrandbits(32).to_bytes(4, "big"))
    return ctx.rng.getrandbits(32)

WORKER_CALLS = {f"movie.vfn_{slot}": model(worker_call, args=("r3",)) for slot in range(42)}

def worker_inputs(t):
    movie = t.alloc(64, "movie")
    t.w32(movie, t.vtable("movie", slots=42))
    t.args(r3=movie)
