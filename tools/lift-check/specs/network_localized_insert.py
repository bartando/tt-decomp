from liftcheck.spec import *
FUNCTION = "localizedTextInsert"
ADDRESS = 0x8240A498
SOURCE = "src/rage/data/localized_text.cpp"
TRIALS = 400
CALLS = {"rage_Alloc": alloc()}
def inputs(t):
    table = t.alloc(12, 'table')
    n = t.rng.choice([1,2,3,7,16])
    buckets = t.alloc(n * 4, 'buckets', fill='zero')
    t.w32(table, n)
    t.w32(table + 4, buckets)
    t.w32(table + 8, t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
    target = t.u32()
    for i in range(n):
        previous = buckets + i * 4
        for j in range(t.rng.randrange(4)):
            node = t.alloc(12, 'node')
            t.w32(previous, node)
            t.w32(node, target if t.rng.random() < 0.25 else t.u32())
            previous = node + 8
        t.w32(previous, 0)
    value = t.alloc(24,'text value')
    t.args(r3=table, r4=target, r5=value)
