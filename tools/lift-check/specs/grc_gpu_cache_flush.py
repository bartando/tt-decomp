"""Compare cache effects directly: coherent-window boundaries, partial/empty lines,
unrolled eight-line groups, and ranges crossing the 32-bit address wrap."""
FUNCTION = 'rage_EEC0'
ADDRESS = 0x8235EEC0
SOURCE = 'src/graphics/grc_cache.cpp'
TRIALS = 900
CACHE_EFFECTS = True


def inputs(t):
    r = t.rng
    start = r.choice([0, 1, 127, 128, 0x7F0FFFFF, 0x7F100000,
                      0x7F100001, 0x86FFFFFF, 0x87000000, 0xFFFFFF80,
                      0xFFFFFFFF, 0x90000000 + r.randrange(0x1000000)])
    length = r.choice([0, 1, 2, 63, 127, 128, 129, 255, 1023, 1024, 1025, r.randrange(4096)])
    for page in {start & ~4095, ((start + length) & 0xFFFFFFFF) & ~4095}:
        if page < 0xFFFF0000:  # The checker already maps its scratch page here.
            t.map(page, 4096, f'cache backing {page:x}')
    t.args(r3=start, r4=(start + length) & 0xFFFFFFFF)
