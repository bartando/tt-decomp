/**
 * graphics/grc_device.cpp — Graphics Device Lifecycle and Sampler State
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Core graphics device functions:
 *   - grcDevice_shutdown    @ 0x8214FA58 — Primary shutdown sequence
 *   - grcDevice_shutdownAlt @ 0x821540D0 — Alternate shutdown path
 *   - grcDevice_SetScissorRect @ 0x823537B0 — scissor commands, including tiled rendering
 *   - grcDevice_setSamplerMinFilter @ 0x82355418 — Xenos texture fetch state
 *   - grcDevice_setSamplerMagFilter @ 0x823555A8 — Xenos texture fetch state
 *   - grcDevice_setSamplerMaxAnisotropy @ 0x82355828 — Xenos texture fetch state
 *   - grcDevice_SetTexture          @ 0x82359940 — bind a texture to a fetch slot
 *   - grcDevice_ReserveCommandSpace @ 0x82359E80 — carve space out of the command ring
 *
 * Note: grcDevice_beginScene lives in grc_render.cpp alongside grcDevice_clear.
 */

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* ── External Dependencies ────────────────────────────────────────────────── */

/* Global singleton pointers */
extern void* g_pCurrentViewport;            /* @ 0x825EBAA0 — current grcViewport */

/* Memory management */
extern void sysMemAllocator_Free(void* ptr);             /* @ 0x820C00C0 — sysMemFree */
extern void rage_free(void* ptr);                        /* @ 0x820C00C0 — rage memory free */

/* Device management functions */
extern void grmShaderGroup_destroy(void* pObj);    /* @ 0x82445BF8 — Destroy shader group (refcounted) */
extern void grcTextureDictionary_destroy(void* pCache); /* @ 0x824456A8 — Destroy texture dictionary */
extern void grcDevice_cleanupInternal(void* pDevice);   /* @ 0x82151068 — Cleanup internal device struct */
extern void grcDevice_releaseSharedResources(void);      /* @ 0x8214F338 — Release shared grc resources */
extern void grcDeviceXenon_teardown(void* pTarget);      /* @ 0x82366CA0 — Full GPU teardown (VdShutdownEngines) */
extern void _locale_register(void* pLocale, uint32_t flags);  /* @ 0x820C02D0 */
extern void thunk_DbgBreakPoint(void);             /* @ 0x82566B70 */
extern void grcDevice_setRenderTarget(void* pDevice, int32_t arg); /* @ 0x82357400 — Set active render target */

/* Forward declaration — defined below */
void grcDevice_shutdownAlt(void);

/* ── Global device-state pointers (extern, defined in globals) ───────────── */

extern uint32_t g_grcDeviceState[100];       /* @ 0x825EBB8C — device state flags array */
extern void*    g_pGrcDeviceObj __asm__("_g_binkVideoPlayer");  /* @ 0x825EB988, defined in globals.c */
extern void*    g_pGrcDeviceAlt;             /* @ 0x825EBA9C — alternate device object pointer */
extern void*    g_pGrcTextureCache;          /* @ 0x825EBC40 — texture cache pointer */
extern void*    g_grcRenderObjects[2];       /* @ 0x82617E60 — render object pair */
extern void*    g_grcRefCountedObjs[4];      /* @ 0x826063E8 — refcounted render objects (2 pairs) */

/* ── Structure Definitions ────────────────────────────────────────────────── */

typedef struct {
    void**   vtable;             /* +0 */
    uint8_t  _pad[4];
    uint16_t m_refCount;         /* +6 */
} RenderObject;


/* ═══════════════════════════════════════════════════════════════════════════
 * grcDevice_shutdown @ 0x8214FA58 | size: 0x1D4 (468 bytes)
 *
 * Primary graphics device shutdown sequence:
 *   1. Clear device state flags
 *   2. Destroy render objects with reference counting
 *   3. Free texture cache
 *   4. Call alternate shutdown path
 *   5. Destroy texture cache object
 *   6. Clean up internal device structures
 *   7. Shutdown graphics core
 *   8. Release render target with reference counting
 *
 * This is the main teardown path called during normal game shutdown.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grcDevice_shutdown(void)
{
    /* 1. Clear device state flag at index 99 (+396). */
    g_grcDeviceState[99] = 0;

    /* Check and clear first state flag; reset render target if it was set. */
    if (g_grcDeviceState[0] != 0) {
        g_grcDeviceState[0] = 0;
        grcDevice_setRenderTarget(g_pGrcDeviceObj, 0);
    }

    /* 2. Destroy shader group and free associated texture data. */
    if (g_grcRenderObjects[0] != NULL) {
        grmShaderGroup_destroy(g_grcRenderObjects[0]);
        g_grcRenderObjects[0] = NULL;
    }

    if (g_grcRenderObjects[1] != NULL) {
        sysMemAllocator_Free(g_grcRenderObjects[1]);
        g_grcRenderObjects[1] = NULL;
    }

    /* 3. Call alternate shutdown path (HUD overlay cleanup). */
    grcDevice_shutdownAlt();

    /* 4. Destroy texture cache. */
    if (g_pGrcTextureCache != NULL) {
        grcTextureDictionary_destroy(g_pGrcTextureCache);
        g_pGrcTextureCache = NULL;
    }

    /* 5. Clean up internal device structures.
     *    These are two adjacent device structs at 0x825EBB98 and 0x825EBBA0. */
    grcDevice_cleanupInternal((void*)((uint8_t*)&g_grcDeviceState[3]));   /* +0x0C from base */
    grcDevice_cleanupInternal((void*)((uint8_t*)&g_grcDeviceState[5]));   /* +0x14 from base */

    /* 6. Release shared graphics resources (global shader/texture refs). */
    grcDevice_releaseSharedResources();

    /* 7. Release refcounted render objects (2 pairs of 2). */
    for (int i = 0; i < 4; i++) {
        RenderObject* pObj = (RenderObject*)g_grcRefCountedObjs[i];
        if (pObj != NULL) {
            pObj->m_refCount--;

            if (pObj->m_refCount == 0) {
                /* Call destructor (vtable slot 0) with flags=1. */
                typedef void (*DtorFn)(void*, int);
                ((DtorFn)pObj->vtable[0])(pObj, 1);
            } else {
                thunk_DbgBreakPoint();  /* Unexpected refcount */
            }

            g_grcRefCountedObjs[i] = NULL;
        }
    }

    /* 8. Release the primary device render target with reference counting. */
    if (g_pGrcDeviceObj != NULL) {
        uint32_t* pTargetData = (uint32_t*)g_pGrcDeviceObj;
        uint32_t refCount = pTargetData[3];  /* +12 */

        if (refCount == 1) {
            grcDeviceXenon_teardown(g_pGrcDeviceObj);

            /* Free locale data (allocation header at -4). */
            void* pLocale = *(void**)((uint8_t*)g_pGrcDeviceObj - 4);
            _locale_register(pLocale, 0x24800000);  /* lis r4, 9344 */

            g_pGrcDeviceObj = NULL;
        } else {
            pTargetData[3] = refCount - 1;

            if (refCount - 1 == 0) {
                thunk_DbgBreakPoint();
            }

            g_pGrcDeviceObj = NULL;
        }
    }
}


/* ═══════════════════════════════════════════════════════════════════════════
 * grcDevice_shutdownAlt @ 0x821540D0 | size: 0x58 (88 bytes)
 *
 * Alternate shutdown path that handles HUD overlay cleanup:
 *   1. Check if HUD overlay pointer matches device pointer
 *   2. Clear HUD overlay pointer if they match
 *   3. Free the device memory
 *   4. Clear device pointer
 *
 * This is called as part of the main shutdown sequence and handles the
 * specific case where the device is also registered as the HUD overlay.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grcDevice_shutdownAlt(void)
{
    void* pDevice = g_pGrcDeviceAlt;

    if (pDevice != NULL) {
        /* If this device is also the HUD overlay, clear that reference. */
        if (g_pCurrentViewport == pDevice) {
            g_pCurrentViewport = NULL;
        }

        /* Free the device memory. */
        rage_free(pDevice);
    }

    /* Clear device pointer. */
    g_pGrcDeviceAlt = NULL;
}

extern "C" void* rage_A980(void* device); // @ 0x8235A980 — refill the command buffer, return its cursor

// Xenon ABI: r3 = device, r4..r7 = signed left/top/right/bottom (exclusive bounds).
// The cursor points at the last written word: every command store preincrements it.
// Tiled rendering is valid only when each nonzero bound render target matches its
// tiled counterpart. It intersects the scissor with each tile and restores the bin
// mask afterward. Coordinates truncate to 14 bits; window offsets use 15 bits.
// @ 0x823537B0
extern "C" void grcDevice_SetScissorRect(void* device, int32_t left, int32_t top,
                                        int32_t right, int32_t bottom) {
    uint8_t* state = static_cast<uint8_t*>(device);
    const auto field = [state](uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(state + offset);
    };
    auto* command = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(field(0)));
    if (field(0) > field(8)) {
        command = static_cast<uint32_t*>(rage_A980(device));
    }
    const auto emit = [&command](uint32_t word) { *++command = word; };
    const auto packScissor = [](int32_t x, int32_t y) {
        return (static_cast<uint32_t>(x) & 0x3FFFu) | ((static_cast<uint32_t>(y) & 0x3FFFu) << 16);
    };

    bool tiled = (state[10432] & 0x10) != 0;
    for (uint32_t i = 0; tiled && i < 5; ++i) {
        const uint32_t target = field(12536 + i * 4);
        if (target != 0 && target != field(12976 + i * 4)) {
            tiled = false;
        }
    }

    if (!tiled) {
        // Type-0 write: PA_SC_WINDOW_OFFSET, WINDOW_SCISSOR_TL and BR.
        emit(0x00022080);
        emit(0);
        emit(packScissor(left, top));
        emit(packScissor(right, bottom));
    } else {
        for (uint32_t i = 0; i < field(12996); ++i) {
            const uint32_t tile = 13000 + i * 16;
            int32_t clipLeft = static_cast<int32_t>(field(tile));
            int32_t clipTop = static_cast<int32_t>(field(tile + 4));
            int32_t clipRight = static_cast<int32_t>(field(tile + 8));
            int32_t clipBottom = static_cast<int32_t>(field(tile + 12));
            if (left > clipLeft) clipLeft = left;
            if (top > clipTop) clipTop = top;
            if (right < clipRight) clipRight = right;
            if (bottom < clipBottom) clipBottom = bottom;
            if (clipLeft >= clipRight || clipTop >= clipBottom) {
                clipLeft = clipTop = clipRight = clipBottom = 0;
            }

            // PPC slw uses six shift bits and yields zero for shifts 32..63.
            const uint32_t shift = (i * 2) & 63u;
            emit(0xC0015000); // SET_BIN_MASK, two bits per tile
            emit(shift < 32 ? 3u << shift : 0);
            emit(0);
            emit(0xC0032D01); // SET_CONSTANT: window offset and scissor registers
            emit(0x00040080);
            const uint32_t offsetX = (0u - field(tile + 240)) & 0x7FFFu;
            const uint32_t offsetY = (0u - field(tile + 244)) & 0x7FFFu;
            emit(offsetX | (offsetY << 16));
            emit(packScissor(clipLeft, clipTop));
            emit(packScissor(clipRight, clipBottom));

            field(0) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(command));
            if (field(0) > field(8)) {
                command = static_cast<uint32_t*>(rage_A980(device));
            }
        }
        emit(0xC0015000);
        const uint32_t mask = field(12960);
        emit(mask != 0 ? mask : 0xFFFFFFFFu);
        emit(0);
    }

    field(0) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(command));
    *reinterpret_cast<uint64_t*>(state + 32) |= UINT64_C(0x3800);
}

extern const uint32_t g_grcAnisoFilterTable[17];  // @ 0x82065D10

// @ 0x82355418
void grcDevice_setSamplerMinFilter(void* device, uint32_t sampler, uint32_t filter) {
    // Xenon ABI: r3 = device, r4 = sampler, r5 = D3D filter value; no return value.
    // Previously mislabeled phArticulatedCollider_5418_p42. These are Xenos fetch
    // constants: word 3 has min_filter[22:21] and aniso_filter[27:25], while
    // word 4 has min_aniso_walk[11] and the volume filter bits [1:0].
    uint8_t* state = static_cast<uint8_t*>(device);
    uint32_t* fetch = reinterpret_cast<uint32_t*>(state + (sampler + 48u) * 24u);
    uint32_t word3 = fetch[3];
    uint32_t word4 = fetch[4];
    uint32_t anisotropic = filter >> 2;

    // The shared anisotropy field also depends on the previous mag_aniso_walk.
    // Preserve the PPC's subtract/andc mask, including for raw filter values.
    uint32_t anisoMask = (((word4 >> 10) & 1u) | anisotropic) - 1u;
    uint32_t anisoFilter = g_grcAnisoFilterTable[state[12020u + sampler]] & ~anisoMask;
    word4 = (word4 & ~0x800u) | ((anisotropic << 11) & 0x800u);
    fetch[4] = word4;

    uint32_t packedFilter = (anisoFilter << 4) | anisotropic | filter;
    word3 = (word3 & ~0x0E600000u) | ((packedFilter << 21) & 0x0E600000u);
    fetch[3] = word3;

    // Compress the low bits of mag/min into vol_mag/vol_min. The cached byte
    // selects automatic derivation (bits >= 2 clear) or an explicit override.
    uint32_t volumeFilters = ((word3 >> 19) & 1u) | ((word3 >> 20) & 2u);
    uint32_t volumeOverride = state[12098u + sampler];
    uint32_t volumeMask = (volumeOverride >> 2) - 1u;
    uint32_t volume = (volumeFilters & volumeMask) + (volumeOverride & ~volumeMask);
    fetch[4] = (word4 & ~3u) | (volume & 3u);

    // srd uses the low seven shift bits and yields zero for shifts 64..127.
    // Guard the C++ shift so that those inputs never invoke undefined behavior.
    uint32_t shift = sampler & 127u;
    uint64_t dirtyBit = shift < 64u ? (UINT64_C(0x8000000000000000) >> shift) : 0;
    uint64_t* dirtySamplers = reinterpret_cast<uint64_t*>(state + 32);
    *dirtySamplers |= dirtyBit;
}

// @ 0x823555A8
void grcDevice_setSamplerMagFilter(void* device, uint32_t sampler, uint32_t filter) {
    uint8_t* state = static_cast<uint8_t*>(device);
    uint32_t* fetch = reinterpret_cast<uint32_t*>(state + (sampler + 48u) * 24u);
    uint32_t word3 = fetch[3];
    uint32_t word4 = fetch[4];
    uint32_t anisotropic = filter >> 2;

    // The shared anisotropy field also depends on the previous min_aniso_walk.
    uint32_t anisoMask = (((word4 >> 11) & 1u) | anisotropic) - 1u;
    uint32_t anisoFilter = g_grcAnisoFilterTable[state[12020u + sampler]] & ~anisoMask;
    word4 = (word4 & ~0x400u) | ((anisotropic << 10) & 0x400u);
    fetch[4] = word4;

    uint32_t packedFilter = (anisoFilter << 6) | anisotropic | filter;
    word3 = (word3 & ~0x0E180000u) | ((packedFilter << 19) & 0x0E180000u);
    fetch[3] = word3;

    uint32_t volumeFilters = ((word3 >> 19) & 1u) | ((word3 >> 20) & 2u);
    uint32_t volumeOverride = state[12098u + sampler];
    uint32_t volumeMask = (volumeOverride >> 2) - 1u;
    uint32_t volume = (volumeFilters & volumeMask) + (volumeOverride & ~volumeMask);
    fetch[4] = (word4 & ~3u) | (volume & 3u);

    // srd uses seven shift bits and returns zero for shifts 64..127.
    uint32_t shift = sampler & 127u;
    uint64_t dirtyBit = shift < 64u ? (UINT64_C(0x8000000000000000) >> shift) : 0;
    uint64_t* dirtySamplers = reinterpret_cast<uint64_t*>(state + 32);
    *dirtySamplers |= dirtyBit;
}

// @ 0x82355828
void grcDevice_setSamplerMaxAnisotropy(void* device, uint32_t sampler, uint32_t anisotropy) {
    uint8_t* state = static_cast<uint8_t*>(device);
    uint32_t* fetch = reinterpret_cast<uint32_t*>(state + (sampler + 48u) * 24u);
    if (fetch[4] & 0xC00u) {
        uint32_t anisoFilter = g_grcAnisoFilterTable[anisotropy];
        fetch[3] = (fetch[3] & ~0x0E000000u) | ((anisoFilter << 25) & 0x0E000000u);

        // srd uses seven shift bits and returns zero for shifts 64..127.
        uint32_t shift = sampler & 127u;
        uint64_t dirtyBit = shift < 64u ? (UINT64_C(0x8000000000000000) >> shift) : 0;
        *reinterpret_cast<uint64_t*>(state + 32) |= dirtyBit;
    }
    state[12020u + sampler] = static_cast<uint8_t>(anisotropy);
}

extern "C" void grcTexture_ReleaseResource(void* texture); // @ 0x82352708

// Bind `texture` (its header holds a fetch constant at +0x10..+0x24) to fetch
// slot `slot`: copy it into the device's fetch constant, keeping the device's
// own clamp/filter bits, clamp the mip range to the slot's limits and mark the
// slot dirty. The previously bound texture drops a reference (and its last-use
// fence) and is released when nothing else holds it.
// @ 0x82359940
extern "C" void grcDevice_SetTexture(void* device, uint32_t slot, void* texture) {
    uint8_t* state = static_cast<uint8_t*>(device);
    auto** bound = reinterpret_cast<uint32_t**>(state + (slot + 3176u) * 4u);
    auto* previous = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(*reinterpret_cast<uint32_t*>(bound)));
    constexpr uint32_t kReference = 0x80000;
    // Physical addresses at or above 0x1E00000 sit in the 4KB-offset aperture.
    const auto physical = [](uint32_t address) { return address + (((address >> 20) + 0x200) & 0x1000); };

    if (texture != nullptr) {
        auto* header = static_cast<uint32_t*>(texture);
        uint32_t* fetch = reinterpret_cast<uint32_t*>(state + (slot + 48u) * 24u);
        header[0] += kReference;
        const uint32_t old1 = fetch[1], old3 = fetch[3], old4 = fetch[4], old5 = fetch[5];
        fetch[0] = (header[4] & ~0x003FFC00u) | (fetch[0] & 0x003FFC00u);
        fetch[1] = (physical(header[5]) & ~0xE0000800u) | (old1 & 0xE0000800u);
        fetch[2] = header[6];
        fetch[4] = old4;
        fetch[3] = (header[7] & ~0x7FF80000u) | (old3 & 0x7FF80000u);
        fetch[5] = (physical(header[9]) & ~0xE00001FFu) | (old5 & 0xE00001FFu);
        uint32_t minMip = (header[8] >> 2) & 0xF;
        const uint32_t slotMin = state[12046 + slot];
        if (minMip <= slotMin) {
            minMip = slotMin;
        }
        uint32_t word4 = (fetch[4] & ~0x3Cu) | (minMip << 2);
        fetch[4] = word4;
        uint32_t maxMip = (header[8] >> 6) & 0xF;
        const uint32_t slotMax = state[12072 + slot];
        if (maxMip >= slotMax) {
            maxMip = slotMax;
        }
        fetch[4] = (word4 & ~0x3C0u) | (maxMip << 6);
        auto& dirty = *reinterpret_cast<uint64_t*>(state + 0x20);
        dirty |= slot < 64 ? 0x8000000000000000ull >> slot : 0;
    }
    *reinterpret_cast<uint32_t*>(bound) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(texture));

    if (previous != nullptr) {
        const uint32_t references = previous[0] - kReference;
        previous[1] = *reinterpret_cast<uint32_t*>(state + 10396);
        previous[0] = references;
        if ((references & 0x00F800FFu) == 0) {
            grcTexture_ReleaseResource(previous);
        }
    }
}

extern "C" void grcDevice_CommitCommandSpace(void* device, uint32_t end, uint32_t sequence); // @ 0x82359DC0

// Reserve space in the device's command ring (all fields are 32-bit addresses):
// +14004/+14008 ring start/end, +14012 minimum block, +14016 cursor in the
// current segment, +14020 wrap sequence, +14024 secondary cursor, +14028 its
// limit, +13536/+13540 the GPU's read fence and the sequence it belongs to.
// `aligned` (bit 0 of flags) asks for `*size` bytes at `alignment` without
// wrapping; otherwise the block is 32-byte aligned, at least the ring minimum,
// and *size is set to what was reserved. Returns 0 if the GPU still owns the space.
// @ 0x82359E80
extern "C" uint32_t grcDevice_ReserveCommandSpace(void* /*unused*/, void* device, uint32_t flags,
                                                  uint32_t* size, uint32_t alignment) {
    uint8_t* state = static_cast<uint8_t*>(device);
    const auto field = [state](uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(state + offset);
    };
    uint32_t words = *size >> 2;
    uint32_t cursor = field(14016);

    if ((flags & 1) != 0) {
        if (cursor == 0) {
            cursor = field(4) + 52;
        }
        const uint32_t mask = ~(alignment - 1);
        const uint32_t sequence = field(14020);
        const uint32_t bytes = words * 4;
        uint32_t start = (cursor + alignment - 1) & mask;
        uint32_t end = bytes + start;
        if (end <= field(14008)) {
            if (const uint32_t fence = field(13536); fence != 0) {
                const int32_t lag = static_cast<int32_t>(field(13540) - sequence);
                if (lag == -1 || (lag == 0 && fence < end)) {
                    return 0;
                }
            }
            field(14016) = end;
            grcDevice_CommitCommandSpace(device, end, sequence);
            return start;
        }
        start = (field(14024) + alignment - 1) & mask;
        end = bytes + start;
        if (const uint32_t fence = field(13536); fence != 0) {
            const int32_t lag = static_cast<int32_t>(field(13540) - sequence - 1);
            if (lag == -1 || (lag == 0 && fence < end)) {
                return 0;
            }
        }
        if (end > field(14028)) {
            return 0;
        }
        field(14024) = end;
        grcDevice_CommitCommandSpace(device, end, sequence + 1);
        return start;
    }

    if (cursor == 0) {
        cursor = field(0) + 4;
    }
    uint32_t base = (cursor + 31) & ~31u;
    if (words == 0) {
        words = 52;
    }
    uint32_t blockWords = field(14012) >> 2;
    if (words > blockWords) {
        blockWords = words;
    }
    const uint32_t blockBytes = blockWords * 4;
    uint32_t end = blockBytes + base;
    if (end > field(14008)) {
        end = field(14008);
    }
    if (static_cast<int32_t>(end - base) >> 2 < static_cast<int32_t>(words)) {
        base = (field(14024) + 31) & ~31u;
        const uint32_t sequence = field(14020) + 1;
        end = blockBytes + base;
        field(14024) = field(14004);
        field(14020) = sequence;
        state[10434] |= 16;
    }
    if (const uint32_t fence = field(13536); fence != 0) {
        const uint32_t fenceSequence = field(13540);
        const uint32_t sequence = field(14020);
        const int32_t lag = static_cast<int32_t>(fenceSequence - sequence);
        if (lag == -1 || (lag == 0 && fence < end)) {
            end = fence;
            if (sequence != fenceSequence || static_cast<int32_t>(end - base) >> 2 < static_cast<int32_t>(words)) {
                return 0;
            }
        }
    }
    grcDevice_CommitCommandSpace(device, end, field(14020));
    *size = static_cast<uint32_t>((static_cast<int32_t>(end - base) >> 2) << 2);
    return base;
}
