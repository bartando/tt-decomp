"""Shared input builder for the rage rsc-constructor specs (not a spec itself).

Builds a datResource and a resource image cut into chunks that each "loaded" at
their own place: pointers written into the image hold saved addresses, and
datResource maps a saved address to its chunk's loaded address.
"""


class Rsc:
    def __init__(self, t, nchunks=None, chunk=None):
        rng = t.rng
        self.t = t
        self.n = nchunks or rng.choice([1, 2, 3, 4])
        self.chunk = chunk or rng.choice([0x800, 0x1000, 0x2000])
        self.saved_base = rng.choice([0x00000000, 0x10000000, 0x50000000, 0x7FF00000])
        self.loaded = [t.alloc(self.chunk, f"chunk{k}") for k in range(self.n)]
        self.used = [0x10] * self.n   # keeps saved address 0 (base 0, chunk 0) unused
        self.addr = t.alloc(0x50, "rsc")
        t.w32(self.addr + 0x04, self.saved_base)
        t.w32(self.addr + 0x4C, self.chunk)
        for k in range(17):
            if k < self.n:
                delta = (self.loaded[k] - (self.saved_base + k * self.chunk)) & 0xFFFFFFFF
            else:
                delta = rng.getrandbits(32)
            t.w32(self.addr + 0x08 + 4 * k, delta)

    def place(self, size, align=4):
        """Reserves `size` bytes in a random chunk with room; returns its loaded address."""
        rng = self.t.rng
        ks = [k for k in range(self.n) if ((self.used[k] + align - 1) & ~(align - 1)) + size <= self.chunk]
        if not ks:
            raise ValueError("resource image full")
        k = rng.choice(ks)
        off = (self.used[k] + align - 1) & ~(align - 1)
        self.used[k] = off + size
        return self.loaded[k] + off

    def saved(self, addr):
        """The saved (pre-fixup) form of a loaded address; 0 stays 0."""
        if addr == 0:
            return 0
        for k, base in enumerate(self.loaded):
            if base <= addr < base + self.chunk:
                return (self.saved_base + k * self.chunk + (addr - base)) & 0xFFFFFFFF
        raise ValueError(f"{addr:#x} is not in the resource image")

    def wptr(self, at, addr):
        """Writes the saved form of `addr` (a loaded address or 0) at `at`."""
        self.t.w32(at, self.saved(addr))

    def string(self, maxlen=12):
        rng = self.t.rng
        s = bytes(rng.randrange(97, 123) for _ in range(rng.randrange(1, maxlen))) + b"\0"
        a = self.place(len(s), 1)
        for i, b in enumerate(s):
            self.t.w8(a + i, b)
        return a

    def maybe(self, addr, p_null=0.2):
        return 0 if self.t.rng.random() < p_null else addr


def build_map(rsc, place_data):
    """An atHashMap image: returns the map's (loaded) address. place_data(rsc) builds
    one entry's data word (a saved value)."""
    t, rng = rsc.t, rsc.t.rng
    m = t.alloc(8, "map")
    nslots = rng.choice([0, 1, 2, 3, 5])
    if nslots == 0 and rng.random() < 0.5:
        t.w32(m, 0)
    else:
        buckets = rsc.place(4 * max(nslots, 1))
        rsc.wptr(m, buckets)
        for s in range(nslots):
            nxt = 0
            for _ in range(rng.choice([0, 0, 1, 2, 3])):
                e = rsc.place(12)
                key = rsc.maybe(rsc.string(), 0.15)
                rsc.wptr(e + 0, key)
                t.w32(e + 4, place_data(rsc))
                rsc.wptr(e + 8, nxt)
                nxt = e
            rsc.wptr(buckets + 4 * s, nxt)
    t.w16(m + 4, nslots)
    t.w16(m + 6, rng.getrandbits(16))
    return m


# lift-check doesn't resolve `// @` markers of free functions inside a namespace
# (rage::X only matches a marker indexed as rage::X, and the header declares them
# unqualified inside `namespace rage {}`), so a callee defined in the TU would be
# inlined into the lift silently. Name them all here, except the function under test:
# lift-check resolves a lambda by its enclosing function's base name, so a lambda in
# the lift would become a call to the lift's own address. Use externs(ADDRESS).
RSC_EXTERNS = {
    "rage::PlaceFaceAnimItemMap": 0x820C2A58,
    "rage::PlaceFaceAnimItem": 0x820C2BA0,
    "rage::PlaceCreatureTypeMap": 0x820C3700,
    "rage::PlaceObservedMap": 0x820CFA40,
    "rage::PlaceAnimObserverHash": 0x820CF778,
    "rage::PlaceAnimObserver": 0x820CF848,
    "rage::PlaceMapKeyString": 0x82387530,
    "rage::PlaceAnimObservedPtr": 0x820CF728,
    "rage::PlaceXmlRootPtr": 0x820CFB88,
    "rage::pcrAnimObserverHash_BuildTree": 0x820CF0F0,
}


def externs(address):
    return {k: v for k, v in RSC_EXTERNS.items() if v != address}
