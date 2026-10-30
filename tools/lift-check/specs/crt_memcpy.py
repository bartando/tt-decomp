"""Exercise the actual CRT entry, never the harness's memcpy model.

Default: a deterministic sample covering all paths, lengths 0..1025, boundary
sizes at every modulo-16 alignment pair, cache offsets, and tight overlaps.
Opt in to the exhaustive matrix with LIFTCHECK_MEMCPY_FULL=1: every length
0..257 at every modulo-16 alignment pair, then all cache-line offset pairs,
longer lengths and overlaps (115232 trials per seed).
The 1056-byte original uses scalar 8/4/1-byte paths, not VMX; modulo-16
coverage also catches assumptions about vector alignment in replacement lifts.
Random contents, guards and address placement vary with the seed. No bytes
are ignored: writes to guards or the source are compared too.
"""
import os

FUNCTION = "memcpy"
ADDRESS = 0x82434100
SOURCE = "src/crt/memory.c"
RET = "r3"
STATIC_INIT = False

SMALL = 258 * 16 * 16
CACHE = 128 * 128
LONG = 768 * 16
OVERLAP = 514 * 16
OVERLAP_EDGES = 3 * 128 * 32
FULL_TRIALS = SMALL + CACHE + LONG + OVERLAP + OVERLAP_EDGES


def full_case(index):
    """(length, destination offset, source offset, shared allocation)."""
    if index < SMALL:
        n, pair = divmod(index, 256)
        da, sa = divmod(pair, 16)
        return n, da, sa, False
    index -= SMALL
    if index < CACHE:
        da, sa = divmod(index, 128)
        # Both bulk paths, cache prologues and tails, prefetch window rollover.
        n = (127, 128, 129, 255, 256, 257, 511, 512,
             513, 1023, 1024, 1025, 2047, 2048, 2049, 4097)[(da + sa) % 16]
        return n, da, sa, False
    index -= CACHE
    if index < LONG:
        n, da = divmod(index, 16)
        return n + 258, da, (da + n) % 16, False
    index -= LONG
    if index < OVERLAP:
        n, variant = divmod(index, 16)
        da = (n + variant) % 128
        # Identity; forward-safe dst<src, including tight/word/cache-line gaps;
        # dst>src as well: compare the original's propagation, not memmove.
        gap = (0, 1, 2, 3, 4, 7, 8, 15, 16, 31, 127, 128,
               -1, -4, -8, -16)[variant]
    else:
        index -= OVERLAP
        edge, pair = divmod(index % OVERLAP_EDGES, 128 * 32)
        n = (255, 256, 1025)[edge]
        da, variant = divmod(pair, 32)
        # Every cache-line offset and gap 1..16 in both directions. In
        # particular gap -12 observes the fourth word's load after store #1.
        gap = variant + 1 if variant < 16 else -(variant - 15)
    return n, da + max(0, -gap), da + max(0, gap), True


def _sample_indices():
    indices = [n * 256 + pair
               for n in (0, 1, 4, 8, 16, 127, 128, 129, 255, 256, 257)
               for pair in range(256)]
    indices += [n * 256 + (n % 16) * 16 + (n // 16) % 16 for n in range(258)]
    # All individual src/dst cache offsets, with two different relative phases.
    indices += [SMALL + da * 128 + (da * 37 + phase) % 128
                for da in range(128) for phase in (0, 1)]
    indices += [SMALL + CACHE + n * 16 + n % 16 for n in range(768)]
    indices += [SMALL + CACHE + LONG + n * 16 + variant
                for n in (0, 1, 7, 8, 16, 127, 128, 129, 255, 256, 257, 513)
                for variant in range(16)]
    indices += [SMALL + CACHE + LONG + OVERLAP + edge * 4096 + da * 32 + variant
                for edge in range(3) for da in range(16) for variant in range(32)]
    return tuple(dict.fromkeys(indices))


SAMPLE_INDICES = _sample_indices()
FULL = os.environ.get("LIFTCHECK_MEMCPY_FULL") == "1"
TRIALS = FULL_TRIALS if FULL else len(SAMPLE_INDICES)


def case(index):
    return full_case(index if FULL else SAMPLE_INDICES[index % len(SAMPLE_INDICES)])


def inputs(t):
    n, da, sa, shared = case(t.index)
    label = f"n={n},dst%128={da % 128},src%128={sa % 128}"
    # Leave readable guards for aligned loads and compare all guard writes.
    size = n + max(da, sa) + 256
    payload = t.rng.randbytes(size)
    # Vary high address bits/relative placement without changing alignments.
    t.alloc(128 * t.rng.randrange(4), "placement", fill="zero", align=128)
    dst = t.alloc(size, f"dst[{label}]", fill=payload, align=128) + 128 + da
    if shared:
        src = dst - da + sa
    else:
        src = t.alloc(size, f"src[{label}]", fill="random", align=128) + 128 + sa
    if n == 0:
        # Guarantee that a bogus zeroing write is observable for empty copies.
        t.w8(dst, 0xA5)
    t.args(r3=dst, r4=src, r5=n)
