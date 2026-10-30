/**
 * memory.c — CRT memory operation implementations
 * Rockstar Presents Table Tennis (Xbox 360)
 *
 * Optimized PPC implementations of memset, memcpy, and memmove.
 * These follow the Xbox 360 CRT pattern of:
 *   1. Byte-by-byte until 4-byte aligned
 *   2. 4-byte word stores in groups of 4 (16 bytes/iter) for bulk
 *   3. Remaining words
 *   4. Tail bytes
 *
 * memcpy additionally uses cache prefetch (dcbt) for large transfers
 * and promotes to 8-byte (doubleword) stores when both src/dst are
 * 8-byte aligned, with a 128-byte unrolled inner loop for large copies.
 */

#include <stddef.h>
#include <stdint.h>

// Forward declaration
void* memcpy(void* dst, const void* src, size_t count);


/**
 * memset @ 0x8242FED0 | size: 0x20
 *
 * Fill `count` bytes starting at `dst` with byte value `c`.
 * Standard C memset semantics.
 */
void* memset(void* dst, int c, size_t count)
{
    unsigned char* p = (unsigned char*)dst;
    unsigned char  v = (unsigned char)c;

    if (count == 0)
        return dst;

    /* Byte fill until 4-byte aligned */
    while (((uintptr_t)p & 3) && count > 0) {
        *p++ = v;
        --count;
    }

    /* Build a 32-bit word from the fill byte and store 16 bytes per iter */
    if (count >= 16) {
        uint32_t  word = v | ((uint32_t)v << 8);
        word          |= word << 16;
        uint32_t* pw   = (uint32_t*)p;
        size_t    iters = count >> 4;
        count          &= 15;
        p              = (unsigned char*)(pw + iters * 4);

        while (iters--) {
            pw[0] = word;
            pw[1] = word;
            pw[2] = word;
            pw[3] = word;
            pw   += 4;
        }
    }

    /* Remaining whole words */
    while (count >= 4) {
        uint32_t word = v | ((uint32_t)v << 8);
        word         |= word << 16;
        *(uint32_t*)p = word;
        p            += 4;
        count        -= 4;
    }

    /* Tail bytes */
    while (count--)
        *p++ = v;

    return dst;
}


/**
 * memmove @ 0x8242FF70 | size: 0x3C
 *
 * Copy `count` bytes from `src` to `dst`, handling overlapping regions
 * correctly. When dst < src (no overlap risk), delegates to memcpy.
 * When dst > src, copies backwards byte-by-byte until 4-byte aligned,
 * then copies whole words descending.
 */
void* memmove(void* dst, const void* src, size_t count)
{
    if (dst == src || count == 0)
        return dst;

    if ((uintptr_t)dst < (uintptr_t)src) {
        /* No overlap risk going forward — use the faster memcpy */
        return memcpy(dst, src, count);
    }

    /* Overlap: copy backwards */
    unsigned char*       d = (unsigned char*)dst + count;
    const unsigned char* s = (const unsigned char*)src + count;

    /* Tail bytes until dst is 4-byte aligned */
    while (((uintptr_t)d & 3) && count > 0) {
        *--d = *--s;
        --count;
    }

    /* Descending word copies */
    if (count >= 4 && (((uintptr_t)s & 3) == 0)) {
        size_t    words = count >> 2;
        count          &= 3;
        uint32_t* dw    = (uint32_t*)d;
        const uint32_t* sw = (const uint32_t*)s;
        while (words--) {
            *--dw = *--sw;
        }
        d = (unsigned char*)dw;
        s = (const unsigned char*)sw;
    }

    /* Remaining bytes */
    while (count--)
        *--d = *--s;

    return dst;
}


/**
 * memcpy @ 0x82434100 | size: 0x420
 *
 * Forward copy with 8-byte destination alignment, then 128-byte cache-line
 * alignment for large transfers. Source alignment selects doubleword, word,
 * or byte-gathered word copies. Cache hints have no observable memory effect.
 *
 * Keep the original load/store order: memmove calls this for dst < src, and
 * callers using dst > src overlap observe the original's chunk propagation.
 * In particular the bulk doubleword loop reads two doublewords ahead, the
 * word loop reads three words before its first store, and the unaligned path
 * gathers four bytes before storing any of them. This is not memmove.
 */
void* memcpy(void* dst, const void* src, size_t count)
{
    unsigned char*       d = (unsigned char*)dst;
    const unsigned char* s = (const unsigned char*)src;

    size_t headBytes = (8 - ((uintptr_t)d & 7)) & 7;
    if (count <= headBytes) {
        while (count--)
            *d++ = *s++;
        return dst;
    }
    count -= headBytes;
    while (headBytes--)
        *d++ = *s++;

    size_t sourceAlignment = (uintptr_t)s & 7;
    if (sourceAlignment == 0) {
        if (count >= 128) {
            size_t cacheHead = (128 - ((uintptr_t)d & 127)) & 127;
            count -= cacheHead;
            while (cacheHead) {
                *(uint64_t*)d = *(const uint64_t*)s;
                d += 8;
                s += 8;
                cacheHead -= 8;
            }
            while (count >= 128) {
                uint64_t*       dq = (uint64_t*)d;
                const uint64_t* sq = (const uint64_t*)s;
                uint64_t a = sq[0];
                uint64_t b = sq[1];
                for (size_t i = 0; i < 14; ++i) {
                    uint64_t c = sq[i + 2];
                    dq[i] = a;
                    a = b;
                    b = c;
                }
                dq[14] = a;
                dq[15] = b;
                d += 128;
                s += 128;
                count -= 128;
            }
        }
        while (count >= 8) {
            *(uint64_t*)d = *(const uint64_t*)s;
            d += 8;
            s += 8;
            count -= 8;
        }
    } else if (sourceAlignment == 4) {
        if (count >= 128) {
            size_t cacheHead = (128 - ((uintptr_t)d & 127)) & 127;
            count -= cacheHead;
            while (cacheHead) {
                *(uint32_t*)d = *(const uint32_t*)s;
                d += 4;
                s += 4;
                cacheHead -= 4;
            }
            while (count >= 128) {
                for (size_t i = 0; i < 8; ++i) {
                    uint32_t*       dw = (uint32_t*)d;
                    const uint32_t* sw = (const uint32_t*)s;
                    uint32_t a = sw[0];
                    uint32_t b = sw[1];
                    uint32_t c = sw[2];
                    dw[0] = a;
                    uint32_t last = sw[3];
                    dw[1] = b;
                    dw[2] = c;
                    dw[3] = last;
                    d += 16;
                    s += 16;
                }
                count -= 128;
            }
        }
        while (count >= 4) {
            *(uint32_t*)d = *(const uint32_t*)s;
            d += 4;
            s += 4;
            count -= 4;
        }
    } else if (count >= 128) {
        size_t cacheHead = (128 - ((uintptr_t)d & 127)) & 127;
        count -= cacheHead;
        while (cacheHead--)
            *d++ = *s++;
        while (count >= 128) {
            for (size_t i = 0; i < 32; ++i) {
                // The union preserves byte order on both Xenon and the host.
                union { uint32_t word; unsigned char bytes[4]; } gathered;
                gathered.bytes[3] = s[3];
                gathered.bytes[2] = s[2];
                gathered.bytes[1] = s[1];
                gathered.bytes[0] = s[0];
                *(uint32_t*)d = gathered.word;
                d += 4;
                s += 4;
            }
            count -= 128;
        }
    }

    while (count--)
        *d++ = *s++;
    return dst;
}
