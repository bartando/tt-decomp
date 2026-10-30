from liftcheck.spec import *

FUNCTION = "crtVsnprintfLocale"
ADDRESS = 0x82432878
SOURCE = "src/crt/printf.cpp"
TRIALS = 1000

def output(c):
    stream = c.r(3)
    data = c.read(stream, 16)
    cursor = int.from_bytes(data[:4], 'big')
    remaining = int.from_bytes(data[4:8], 'big')
    # Script both successful output and exhausted streams, including signed boundaries.
    delta = c.rng.choice([0, 1, 2]) if cursor and 0 < remaining < 32 else 0
    if delta and delta <= remaining:
        c.write(cursor, bytes([0x41]) * delta)
        cursor += delta
        remaining -= delta
    c.write(stream, cursor.to_bytes(4, 'big') + remaining.to_bytes(4, 'big'))
    c.ret(r3=c.rng.choice([-1, 0, 1, 5, 0x7fffffff]))

def errno(c):
    c.ret(r3=c.r(3))

CALLS = {
    "crtOutput": model(output, args=("r3", "r4", "r5", "r6"), deref={"r3": 16}),
    "crtFlushChar": stub(ret=0, args=("r3", "r4"), deref={"r4": 16}),
    "crtErrno": model(lambda c: c.ret(r3=c.alloc(4)), args=()),
    "crtInvalidParameter": stub(ret="void", args=("r3", "r4", "r5", "r6", "r7")),
}

def inputs(t):
    buf = t.alloc(64, "buffer")
    fmt = t.alloc(8, "format")
    args = t.alloc(16, "arguments")
    t.w8(fmt, 0)
    size = t.rng.choice([0, 1, 2, 3, 20, 0x80000000, 0xffffffff])
    t.args(r3=t.rng.choice([0, buf + 8]), r4=size,
           r5=t.rng.choice([0, fmt]), r6=t.u32(), r7=args)
