/**
 * graphics/grc_device.cpp — Graphics Device Lifecycle and Sampler State
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Core graphics device functions:
 *   - grcDevice_shutdown    @ 0x8214FA58 — Primary shutdown sequence
 *   - grcDevice_shutdownAlt @ 0x821540D0 — Alternate shutdown path
 *   - grcDevice_SetScissorRect @ 0x823537B0 — scissor commands, including tiled rendering
 *   - grcDevice_SetAlphaBlendEnable / SetBlendOp / SetSrcBlend / SetDestBlend
 *                                   @ 0x82353AE8/3B88/3C20/3CB8 — RB_BLENDCONTROL
 *   - grcDevice_setSamplerMinFilter @ 0x82355418 — Xenos texture fetch state
 *   - grcDevice_setSamplerMagFilter @ 0x823555A8 — Xenos texture fetch state
 *   - grcDevice_setSamplerMaxAnisotropy @ 0x82355828 — Xenos texture fetch state
 *   - grcDevice_setSamplerMipFilter     @ 0x82355738 — Xenos texture fetch state
 *   - grcDevice_setSamplerAddressU/V/W  @ 0x82355B58/BA8/BF8 — Xenos texture fetch state
 *   - grcDevice_setSamplerTrilinearThreshold @ 0x82355C48 — Xenos texture fetch state
 *   - grcDevice_setSamplerLodBias       @ 0x82355948 — Xenos texture fetch state
 *   - grcDevice_SetViewport         @ 0x82355ED0 — clip and load the viewport transform
 *   - grcDevice_SetZEnable / SetStencilEnable @ 0x82354120/41F0 — RB_DEPTHCONTROL
 *   - grcDevice_SetZWriteEnable     @ 0x82354170 — RB_DEPTHCONTROL
 *   - grcDevice_SetColorWriteEnable @ 0x823547A0 — RB_COLOR_MASK for target 0
 *   - grcDevice_SetAlphaTestEnable  @ 0x82353AA0 — RB_COLORCONTROL
 *   - grcDevice_SetCullMode         @ 0x82353A30 — mode-control low bits (name inferred)
 *   - grcDevice_SetIndices          @ 0x82356210 — bind the index buffer
 *   - grcDevice_SetDepthStencilSurface @ 0x823565F8 — bind the depth surface
 *   - grcDevice_SetStreamSource     @ 0x82356118 — bind a vertex buffer to a stream
 *   - grcDevice_SetRenderTarget     @ 0x82356290 — bind a colour surface to a target slot
 *   - grcDevice_SetPixelShaderConstantF @ 0x82356A70 — upload pixel shader constants 0..19
 *   - grcDevice_BeginDrawPrimitiveUP @ 0x82357630 — queue a draw and allocate its vertices
 *   - grcGpuBuffer_Release          @ 0x82356CF0 — drop a reference, free on the last
 *   - grcGpuResource_Release        @ 0x82356DA8 — drop a reference, free on the last
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
extern const float g_grcLodBiasScale;             // @ 0x82079AF0

// The color half of RB_BLENDCONTROL lives at +0x2CB8; +0x2CBC holds blending
// enabled (bit 31) and separate alpha (bit 30). Without separate alpha the
// alpha half copies the color factors, mapped from color to alpha variants.
static void commitBlendControl(uint8_t* state, uint32_t control) {
    auto word = [state](uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(state + offset);
    };
    if ((word(0x2CBC) & 0x40000000u) == 0) {
        const uint32_t color = control & 0xFFFFu;
        uint32_t alpha = (color & 0x1010u) | (color << 4);
        alpha = ((alpha << 12) | (alpha >> 20)) & 0xFFFF0000u;
        control = (alpha & ~0x10100000u) | color;
    }
    word(0x2D78) = control;
    word(0x2D98) = control;
    word(0x2D9C) = control;
    word(0x2DA0) = control;
    *reinterpret_cast<uint64_t*>(state + 0x28) |= UINT64_C(0x0000001000000000) | 0x1C000000u;
}

// Disabling writes ONE/ZERO/ADD for both halves but keeps the stored factors.
// @ 0x82353AE8
void grcDevice_SetAlphaBlendEnable(void* device, uint32_t enable) {
    auto* state = static_cast<uint8_t*>(device);
    auto& flags = *reinterpret_cast<uint32_t*>(state + 0x2CBC);
    flags = (flags & 0x7FFFFFFFu) | (enable << 31);
    if (enable == 0) {
        commitBlendControl(state, 0x00010001u);
        return;
    }
    commitBlendControl(state, *reinterpret_cast<uint32_t*>(state + 0x2CB8));
}

static void setBlendField(void* device, uint32_t value, uint32_t shift, uint32_t mask) {
    auto* state = static_cast<uint8_t*>(device);
    auto& control = *reinterpret_cast<uint32_t*>(state + 0x2CB8);
    control = (control & ~mask) | ((value << shift) & mask);
    if ((*reinterpret_cast<uint32_t*>(state + 0x2CBC) & 0x80000000u) != 0)
        commitBlendControl(state, control);
}

// @ 0x82353B88
void grcDevice_SetBlendOp(void* device, uint32_t op) {
    setBlendField(device, op, 5, 0x000000E0u);
}

// @ 0x82353C20
void grcDevice_SetSrcBlend(void* device, uint32_t blend) {
    setBlendField(device, blend, 0, 0x0000001Fu);
}

// @ 0x82353CB8
void grcDevice_SetDestBlend(void* device, uint32_t blend) {
    setBlendField(device, blend, 8, 0x00001F00u);
}

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

// Insert a field into one dword of a sampler's fetch constant and mark the
// sampler dirty. srd uses seven shift bits, so samplers 64..127 set no bit.
static void setSamplerFetchField(void* device, uint32_t sampler, uint32_t dword,
                                 uint32_t value, uint32_t shift, uint32_t width) {
    uint8_t* state = static_cast<uint8_t*>(device);
    uint32_t* fetch = reinterpret_cast<uint32_t*>(state + (sampler + 48u) * 24u);
    uint32_t mask = ((1u << width) - 1u) << shift;
    fetch[dword] = (fetch[dword] & ~mask) | ((value << shift) & mask);

    uint32_t bit = sampler & 127u;
    uint64_t dirtyBit = bit < 64u ? (UINT64_C(0x8000000000000000) >> bit) : 0;
    *reinterpret_cast<uint64_t*>(state + 32) |= dirtyBit;
}

// @ 0x82355738
void grcDevice_setSamplerMipFilter(void* device, uint32_t sampler, uint32_t filter) {
    setSamplerFetchField(device, sampler, 3, filter, 23, 2);
}

// Address modes are dword 0's clamp_x/y/z.
// @ 0x82355B58
void grcDevice_setSamplerAddressU(void* device, uint32_t sampler, uint32_t mode) {
    setSamplerFetchField(device, sampler, 0, mode, 10, 3);
}

// @ 0x82355BA8
void grcDevice_setSamplerAddressV(void* device, uint32_t sampler, uint32_t mode) {
    setSamplerFetchField(device, sampler, 0, mode, 13, 3);
}

// @ 0x82355BF8
void grcDevice_setSamplerAddressW(void* device, uint32_t sampler, uint32_t mode) {
    setSamplerFetchField(device, sampler, 0, mode, 16, 3);
}

// Dword 5's tri_clamp.
// @ 0x82355C48
void grcDevice_setSamplerTrilinearThreshold(void* device, uint32_t sampler, uint32_t threshold) {
    setSamplerFetchField(device, sampler, 5, threshold, 3, 2);
}

// The bias arrives as raw float bits (a D3D-style sampler state DWORD) and is
// stored as fetch dword 4's 10-bit fixed-point lod_bias.
// @ 0x82355948
void grcDevice_setSamplerLodBias(void* device, uint32_t sampler, uint32_t biasBits) {
    uint8_t* state = static_cast<uint8_t*>(device);
    uint32_t* fetch = reinterpret_cast<uint32_t*>(state + (sampler + 48u) * 24u);
    float bias;
    __builtin_memcpy(&bias, &biasBits, sizeof bias);
    float scaled = bias * g_grcLodBiasScale;

    // fctidz saturates (NaN gives INT64_MIN); stfiwx keeps the low word.
    uint32_t fixed;
    if (scaled != scaled || scaled <= -0x1p63f) {
        fixed = 0;
    } else if (scaled >= 0x1p63f) {
        fixed = 0xFFFFFFFFu;
    } else {
        fixed = static_cast<uint32_t>(static_cast<int64_t>(scaled));
    }
    fetch[4] = (fetch[4] & ~0x003FF000u) | ((fixed << 12) & 0x003FF000u);

    // srd uses seven shift bits and returns zero for shifts 64..127.
    uint32_t shift = sampler & 127u;
    uint64_t dirtyBit = shift < 64u ? (UINT64_C(0x8000000000000000) >> shift) : 0;
    *reinterpret_cast<uint64_t*>(state + 32) |= dirtyBit;
}

extern "C" void grcTexture_ReleaseResource(void* texture); // @ 0x82352708

extern "C" uint32_t KeGetCurrentProcessType();   // @ 0x82585E9C
extern "C" uint32_t xe_GetCurrentThreadId();     // @ 0x82566B78
extern "C" void rage_AA78(void* gpuDevice, uint32_t* handle);  // @ 0x8235AA78
extern const uint32_t __imp_VdGlobalDevice;      // @ 0x82000730
extern const uint32_t __imp_VdGlobalXamDevice;   // @ 0x82000734

// Drop a reference to a GPU resource. On the last one, hand its handle (+0x08)
// back to the kernel video device (the title's or, in a system process, XAM's)
// and free its data block and itself if it owns them. Returns the references
// left.
// Both resource kinds keep a reference count at +4, a GPU handle at +8, their
// data pointer and a flags word saying which allocations to free.
static uint32_t releaseGpuResource(void* resource, uint32_t dataWord, uint32_t flagsWord,
                                   uint32_t dataFlag, uint32_t dataTag) {
    uint32_t* words = static_cast<uint32_t*>(resource);
    const uint32_t references = --words[1];
    if (references != 0) {
        return references;
    }
    if (words[dataWord] != 0) {
        const uint32_t slot = KeGetCurrentProcessType() == 2 ? __imp_VdGlobalXamDevice : __imp_VdGlobalDevice;
        void* gpuDevice = reinterpret_cast<void*>(static_cast<uintptr_t>(
            *reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(slot))));
        if (gpuDevice != nullptr) {
            uint32_t handle = words[2];
            xe_GetCurrentThreadId();
            if (handle != 0) {
                rage_AA78(gpuDevice, &handle);
            }
        }
        if (words[flagsWord] & dataFlag) {
            _locale_register(reinterpret_cast<void*>(static_cast<uintptr_t>(words[dataWord])), dataTag);
        }
    }
    if (words[flagsWord] & 0x40000000u) {
        _locale_register(resource, 0x24800000);
    }
    return 0;
}

// Name inferred: the smaller sibling of grcGpuResource_Release, with data at
// +0xC and flags at +0x1C. Callers release one of each back to back.
// @ 0x82356CF0
extern "C" uint32_t grcGpuBuffer_Release(void* buffer) {
    return releaseGpuResource(buffer, 0xC / 4, 0x1C / 4, 0x80000000u, 0xB1800000);
}

// @ 0x82356DA8
extern "C" uint32_t grcGpuResource_Release(void* resource) {
    return releaseGpuResource(resource, 0x28 / 4, 0x24C / 4, 0x20000000u, 0xA1800000);
}

extern "C" void grc_5E08(void* device, const void* rect);  // @ 0x82355E08
extern const float g_grcHalf;                       // @ 0x8202D10C

// D3DVIEWPORT9 layout.
struct grcViewportRect {
    uint32_t x, y, width, height;
    float minZ, maxZ;
};

// Clip `viewport` to the bound render target and load the viewport transform
// (scale/offset per axis, depth range) into the shadow constants. The target
// size comes from the surface (color 0, else depth) unless the device's cached
// target set (+0x32B0) still matches, in which case its cached size is used.
// @ 0x82355ED0
extern "C" void grcDevice_SetViewport(void* device, const void* viewport) {
    uint8_t* state = static_cast<uint8_t*>(device);
    const auto* targets = reinterpret_cast<const uint32_t*>(state + 0x30F8);
    const auto* vp = static_cast<const grcViewportRect*>(viewport);
    uint32_t surface = targets[0] != 0 ? targets[0] : targets[4];
    if (surface == 0) {
        return;
    }

    bool cached = (state[0x28C0] & 0x10) != 0;
    const auto* cachedTargets = reinterpret_cast<const uint32_t*>(state + 0x32B0);
    for (int i = 0; cached && i < 5; ++i) {
        cached = cachedTargets[i] == targets[i] || targets[i] == 0;
    }
    uint32_t targetWidth, targetHeight;
    if (cached) {
        targetWidth = *reinterpret_cast<const uint32_t*>(state + 0x34A8);
        targetHeight = *reinterpret_cast<const uint32_t*>(state + 0x34AC);
    } else {
        const uint32_t size = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(surface))[6];
        targetWidth = (size & 0x1FFF) + 1;
        targetHeight = ((size >> 13) & 0x1FFF) + 1;
    }

    const uint32_t x = vp->x, y = vp->y;
    const uint32_t right = x + vp->width < targetWidth ? x + vp->width : targetWidth;
    const uint32_t bottom = y + vp->height < targetHeight ? y + vp->height : targetHeight;
    const uint32_t width = right - x, height = bottom - y;
    auto* clipped = reinterpret_cast<grcViewportRect*>(state + 0x3208);
    clipped->x = x;
    clipped->y = y;
    clipped->width = width;
    clipped->height = height;
    clipped->minZ = vp->minZ;
    clipped->maxZ = vp->maxZ;
    grc_5E08(device, state + 0x3220);

    auto* transform = reinterpret_cast<float*>(state + 0x2D48);
    const float halfWidth = static_cast<float>(width) * g_grcHalf;
    const float halfHeight = static_cast<float>(height) * g_grcHalf;
    transform[0] = halfWidth;
    transform[1] = static_cast<float>(x) + halfWidth;
    transform[2] = -halfHeight;
    transform[3] = static_cast<float>(y) + halfHeight;
    transform[4] = vp->maxZ - vp->minZ;
    transform[5] = vp->minZ;
    *reinterpret_cast<uint64_t*>(state + 0x28) |= UINT64_C(0x0001F80000000000);
}

// Copy vertex shader float constants (one 16-byte register each) and mark
// every touched group of four registers dirty for the next device flush.
// @ 0x82356928
extern "C" void grcDevice_SetVertexShaderConstantF(void* device, uint32_t first, const void* constants,
                                                    uint32_t count) {
    auto* state = static_cast<uint8_t*>(device);
    const auto* src = static_cast<const uint8_t*>(constants);
    const uint32_t originalCount = count;
    uintptr_t address = reinterpret_cast<uintptr_t>(state) + ((first + 120u) << 4);
    auto* dst = reinterpret_cast<uint8_t*>(address & ~uintptr_t(15));

    // The four-register loop loads all four vectors before storing any of them.
    while (count >= 4) {
        uint8_t values[64];
        for (uint32_t i = 0; i < 64; ++i) values[i] = src[i];
        for (uint32_t i = 0; i < 64; ++i) dst[i] = values[i];
        src += 64;
        dst += 64;
        count -= 4;
    }
    for (uint32_t n = 0; n < count; ++n) {
        uint8_t value[16];
        for (uint32_t i = 0; i < 16; ++i) value[i] = src[i];
        for (uint32_t i = 0; i < 16; ++i) dst[i] = value[i];
        src += 16;
        dst += 16;
    }

    const uint32_t firstGroup = first >> 2;
    const uint32_t lastGroup = (first + originalCount - 1u) >> 2;
    const uint32_t span = (lastGroup - firstGroup) & 127u;
    const uint64_t mask = UINT64_C(0x8000000000000000);
    const uint64_t range = span >= 63 ? UINT64_MAX : static_cast<uint64_t>(static_cast<int64_t>(mask) >> span);
    *reinterpret_cast<uint64_t*>(state + 0x10) |= (firstGroup & 127u) < 64 ? range >> (firstGroup & 127u) : 0;
}

// The game's build is specialized for its only call shape: every caller passes
// first = 0 and count = 20, and the body ignores both. Pixel constants live
// after the 256 vertex ones; their dirty groups are the second mask word.
// @ 0x82356A70
extern "C" void grcDevice_SetPixelShaderConstantF(void* device, uint32_t /*first*/,
                                                   const void* constants, uint32_t /*count*/) {
    auto* state = static_cast<uint8_t*>(device);
    const auto* src = static_cast<const uint8_t*>(constants);
    auto* dst = reinterpret_cast<uint8_t*>(reinterpret_cast<uintptr_t>(state + 0x1780) & ~uintptr_t(15));

    // Each group of four registers is loaded in full before any of it is stored.
    for (uint32_t group = 0; group < 5; ++group) {
        uint8_t values[64];
        for (uint32_t i = 0; i < 64; ++i) values[i] = src[i];
        for (uint32_t i = 0; i < 64; ++i) dst[i] = values[i];
        src += 64;
        dst += 64;
    }
    *reinterpret_cast<uint64_t*>(state + 0x18) |= UINT64_C(0xF800000000000000);
}

// Device bindings count as 0x80000 in a resource's first word. Dropping one
// stamps the current fence; the resource goes once no references remain.
constexpr uint32_t kDeviceReference = 0x80000;

static void dropDeviceReference(uint8_t* state, uint32_t* resource) {
    if (resource == nullptr) {
        return;
    }
    const uint32_t references = resource[0] - kDeviceReference;
    resource[1] = *reinterpret_cast<uint32_t*>(state + 10396);
    resource[0] = references;
    if ((references & 0x00F800FFu) == 0) {
        grcTexture_ReleaseResource(resource);
    }
}

// Insert `value` into one register word and mark its dirty bits.
static void setRegisterField(uint8_t* state, uint32_t offset, uint32_t value, uint32_t shift,
                             uint32_t width, uint64_t dirty28, uint64_t dirty30) {
    auto& reg = *reinterpret_cast<uint32_t*>(state + offset);
    const uint32_t mask = ((1u << width) - 1u) << shift;
    reg = (reg & ~mask) | ((value << shift) & mask);
    *reinterpret_cast<uint64_t*>(state + 0x28) |= dirty28;
    if (dirty30 != 0) {
        *reinterpret_cast<uint64_t*>(state + 0x30) |= dirty30;
    }
}

// @ 0x82353A30
extern "C" void grcDevice_SetCullMode(void* device, uint32_t mode) {
    setRegisterField(static_cast<uint8_t*>(device), 0x2D88, mode, 0, 3, UINT64_C(1) << 32, 0);
}

// @ 0x82353AA0
extern "C" void grcDevice_SetAlphaTestEnable(void* device, uint32_t enable) {
    setRegisterField(static_cast<uint8_t*>(device), 0x2D7C, enable, 3, 1, UINT64_C(1) << 35, 0x40);
}

// @ 0x82354170
extern "C" void grcDevice_SetZWriteEnable(void* device, uint32_t enable) {
    setRegisterField(static_cast<uint8_t*>(device), 0x2D74, enable, 2, 1, UINT64_C(1) << 37, 0);
}

// The mask only applies with a colour target bound; the request is kept for
// the next bind.
// @ 0x823547A0
extern "C" void grcDevice_SetColorWriteEnable(void* device, uint32_t mask) {
    uint8_t* state = static_cast<uint8_t*>(device);
    *reinterpret_cast<uint32_t*>(state + 0x2EB4) = mask;
    if (*reinterpret_cast<uint32_t*>(state + 0x30F8) == 0) {
        mask = 0;
    }
    setRegisterField(state, 0x2D1C, mask, 0, 4, UINT64_C(1) << 59, 0);
}

// RB_DEPTHCONTROL lives at +0x2D74. Without a depth surface both switches
// are written off, but the requested values are kept for the next bind.
static void setDepthControlBit(uint8_t* state, uint32_t requestOffset, uint32_t enable, uint32_t bit) {
    auto word = [state](uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(state + offset);
    };
    word(requestOffset) = enable;
    if (word(0x3108) == 0) {
        enable = 0;
    }
    word(0x2D74) = (word(0x2D74) & ~(1u << bit)) | ((enable << bit) & (1u << bit));
    *reinterpret_cast<uint64_t*>(state + 0x28) |= UINT64_C(1) << 37;
    *reinterpret_cast<uint64_t*>(state + 0x30) |= 0x20;
}

// @ 0x82354120
extern "C" void grcDevice_SetZEnable(void* device, uint32_t enable) {
    setDepthControlBit(static_cast<uint8_t*>(device), 0x2EC4, enable, 1);
}

// @ 0x823541F0
extern "C" void grcDevice_SetStencilEnable(void* device, uint32_t enable) {
    setDepthControlBit(static_cast<uint8_t*>(device), 0x2EC8, enable, 0);
}

extern "C" void grc_36E8(void* device, void* surface); // @ 0x823536E8

// Binding a depth surface without a colour target lets grc_36E8 size the
// viewport from it. Afterwards the Z and stencil switches are reapplied, and
// bit 2 of +0x28C0 records whether every bound surface still matches the cached
// set (an unbound slot matches anything).
// @ 0x823565F8
extern "C" void grcDevice_SetDepthStencilSurface(void* device, void* surface) {
    uint8_t* state = static_cast<uint8_t*>(device);
    auto word = [state](uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(state + offset);
    };
    auto dirty = [state](uint32_t offset) -> uint64_t& {
        return *reinterpret_cast<uint64_t*>(state + offset);
    };
    dropDeviceReference(state, reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(word(0x3108))));
    word(0x3108) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(surface));
    if (surface != nullptr) {
        auto* header = static_cast<uint32_t*>(surface);
        header[0] += kDeviceReference;
        if (word(0x30F8) == 0) {
            grc_36E8(device, surface);
        }
        word(0x2CC8) = header[0x34 / 4];
        word(0x2D80) = header[0x38 / 4];
        state[0x28C2] = static_cast<uint8_t>((state[0x28C2] & 0x7Fu) | ((header[0x38 / 4] << 7) & 0x80u));
        dirty(0x20) |= 0x08000000u;
        dirty(0x28) |= UINT64_C(1) << 34;
        dirty(0x30) |= 0x20;
    } else {
        word(0x2D80) &= 0xFFFFFFF0u;
        state[0x28C2] &= 0x7Fu;
        dirty(0x28) |= UINT64_C(1) << 34;
    }

    bool matchesCache = false;
    if (word(0x32A0) == 0 && (state[0x28C0] & 0x10u) != 0) {
        matchesCache = true;
        for (uint32_t i = 0; i < 5; ++i) {
            const uint32_t bound = word(0x30F8 + i * 4);
            if (word(0x32B0 + i * 4) != bound && bound != 0) {
                matchesCache = false;
                break;
            }
        }
    }
    state[0x28C0] = static_cast<uint8_t>((state[0x28C0] & ~4u) | (matchesCache ? 4u : 0u));
    grcDevice_SetZEnable(device, word(0x2EC4));
    grcDevice_SetStencilEnable(device, word(0x2EC8));
}

// Name inferred: device+0x30F4 sits just before the render targets.
// @ 0x82356210
extern "C" void grcDevice_SetIndices(void* device, void* indices) {
    uint8_t* state = static_cast<uint8_t*>(device);
    if (indices != nullptr) {
        static_cast<uint32_t*>(indices)[0] += kDeviceReference;
    }
    dropDeviceReference(state, reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(
        *reinterpret_cast<uint32_t*>(state + 0x30F4))));
    *reinterpret_cast<uint32_t*>(state + 0x30F4) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(indices));
}

// Bind `buffer` to vertex stream `stream` at `offset` with `stride` bytes per
// vertex. Same reference swap as grcDevice_SetTexture; a non-null bind also
// marks the vertex fetch constants dirty.
// @ 0x82356118
extern "C" void grcDevice_SetStreamSource(void* device, uint32_t stream, void* buffer,
                                          uint32_t offset, uint32_t stride) {
    uint8_t* state = static_cast<uint8_t*>(device);
    if (buffer != nullptr) {
        static_cast<uint32_t*>(buffer)[0] += kDeviceReference;
        *reinterpret_cast<uint64_t*>(state + 0x30) |= 0x400;
    }

    uint32_t* binding = reinterpret_cast<uint32_t*>(state + 0x310C + stream * 8u);
    dropDeviceReference(state, reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(binding[1])));
    binding[1] = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(buffer));
    binding[0] = offset;
    state[0x3190 + stream] = static_cast<uint8_t>(stride >> 2);
}

extern "C" void grc_36E8(void* device, void* surface); // @ 0x823536E8

// Bind a colour surface (slots 0..3), update its packed format and colour-write
// mask, and refresh the tiled-target flag for slot 0. Unlike texture/stream binds,
// the old reference is released BEFORE the new one is acquired, even on a rebind.
// The surface's colour-info word lives at +52; its format is bits 19:16.
// @ 0x82356290 | size: 0x368 (872 bytes)
extern "C" void grcDevice_SetRenderTarget(void* device, uint32_t slot, void* surface) {
    auto* state = static_cast<uint8_t*>(device);
    const auto field = [state](uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(state + offset);
    };
    auto* previous = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(field(12536 + slot * 4u)));
    // Unlike the stream and index binds, the old reference goes first.
    dropDeviceReference(state, previous);
    field(12536 + slot * 4u) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(surface));

    if (surface != nullptr) {
        auto* header = static_cast<uint32_t*>(surface);
        header[0] += kDeviceReference;
        // RB_COLOR0_INFO is followed by another register before COLOR1..3_INFO.
        const uint32_t colorRegister = slot == 0 ? 0 : slot + 1u;
        const uint32_t colorOffset = (2865u + colorRegister) * 4u;
        field(colorOffset) = header[13];
        const uint32_t dirtyIndex = 0x20123u + colorRegister;
        const uint32_t shift = dirtyIndex & 127u;
        auto& dirty = *reinterpret_cast<uint64_t*>(state + 16 + (dirtyIndex >> 16) * 8u);
        const uint64_t dirtyBit = shift < 64 ? UINT64_C(0x8000000000000000) >> shift : 0;
        dirty |= dirtyBit;

        const uint32_t mode = field(12144 + slot * 4u);
        const uint32_t format = (header[13] >> 16) & 15u;
        // The original tests the upper halfword, then adjusts these four formats
        // according to the per-target mode. Preserve its bitwise selection for
        // raw mode values too (slw masks to six bits, yielding zero for 32..63).
        const uint32_t formatShift = (mode * 2u) & 63u;
        const uint32_t formatTest = formatShift < 32 ? 2u << formatShift : 0;
        if ((format == 2 || format == 3 || format == 10 || format == 12) &&
            (formatTest & format) == 0) {
            const uint32_t modeMask = mode - 1u;
            const uint32_t adjusted = (((format + 3u) * 2u) & ~modeMask) |
                                      (((format >> 1) - 3u) & modeMask);
            const uint32_t formatBits = (adjusted & 15u) << 16;
            header[13] = (header[13] & ~0x000F0000u) | formatBits;
            field(colorOffset) = (field(colorOffset) & ~0x000F0000u) | formatBits;
            dirty |= dirtyBit;
        }
    }

    if (slot == 0) {
        void* sizeSurface = surface != nullptr ? surface :
            reinterpret_cast<void*>(static_cast<uintptr_t>(field(12552)));
        if (sizeSurface != nullptr) {
            grc_36E8(device, sizeSurface);
        }
        bool tiled = field(12960) == 0 && (state[10432] & 0x10) != 0;
        for (uint32_t i = 0; tiled && i < 5; ++i) {
            const uint32_t target = field(12536 + i * 4u);
            tiled = target == 0 || target == field(12976 + i * 4u);
        }
        state[10432] = static_cast<uint8_t>((state[10432] & ~4u) | (tiled ? 4u : 0u));
    }
    if (slot < 4) {
        const uint32_t writeMask = field(12536 + slot * 4u) != 0 ? field(11956 + slot * 4u) : 0;
        const uint32_t shift = slot * 4u;
        field(11548) = (field(11548) & ~(15u << shift)) | ((writeMask & 15u) << shift);
        *reinterpret_cast<uint64_t*>(state + 40) |= UINT64_C(0x0800000000000000);
    }
}

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
    // Physical addresses at or above 0x1E00000 sit in the 4KB-offset aperture.
    const auto physical = [](uint32_t address) { return address + (((address >> 20) + 0x200) & 0x1000); };

    if (texture != nullptr) {
        auto* header = static_cast<uint32_t*>(texture);
        uint32_t* fetch = reinterpret_cast<uint32_t*>(state + (slot + 48u) * 24u);
        header[0] += kDeviceReference;
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

    dropDeviceReference(state, previous);
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

extern "C" {
    // The older shader lifts call these masks flushRequired / forceResetFlag.
    extern uint32_t g_grmShaderFx_flushRequired;       // @ 0x825EBB1C
    extern uint32_t g_grmShaderFx_forceResetFlag;      // @ 0x825EBAB4
    extern uint32_t g_grmShaderFx_variantTable[];      // @ 0x825EBBD8 — pending render state
    extern uint32_t g_grcAppliedRenderState[22];      // @ 0x825EBB80
    extern uint32_t g_grcPendingTextureState[24];     // @ 0x825EBB20 — eight 12-byte entries
    extern uint32_t g_grcAppliedTextureState[24];     // @ 0x825EBAB8
    extern uint8_t g_grcUsePendingTexture;            // @ 0x825C89E5
    extern uint32_t g_grcTextureParameter;            // @ 0x825EB980
    extern void* g_grcDefaultTexture;                 // @ 0x825EBA20
    extern uint32_t g_grcFormatId;                    // @ 0x825C9030
    extern const uint32_t g_grcCullModeTable[3];       // @ 0x825D4CC4
    extern const uint32_t g_grcColorWriteMaskTable[16]; // @ 0x825D4CD0
    extern const uint32_t g_grcCompareFuncTable[8];    // @ 0x825D4D10
    extern const uint32_t g_grcFillModeTable[3];       // @ 0x825D4D30
    extern const uint32_t g_grcFormatCompareTable[8];  // @ 0x825D4D3C
    void hudFlashBase_A830_g(void* context, uint32_t parameter, void* texture); // @ 0x8215A830
}

// Publish dirty texture/render state before drawing. Device callbacks are stored
// directly in the device, at the byte offsets below (there is no vtable indirection).
// Xenon ABI: no arguments or return value. All state words and texture handles
// retain their original 32-bit layout. Reload globals across callbacks, as PPC does.
// @ 0x8215B138
extern "C" void grcDevice_FlushRenderState() {
    uint32_t textureDirty = g_grmShaderFx_forceResetFlag;
    for (uint32_t slot = 0; slot < 8; ++slot) {
        if ((textureDirty & (1u << (slot * 4))) != 0) {
            uint32_t texture = g_grcPendingTextureState[slot * 3];
            g_grcAppliedTextureState[slot * 3] = texture;
            if (g_grcUsePendingTexture == 0) {
                texture = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(g_grcDefaultTexture));
            }
            if (slot == 0) {
                hudFlashBase_A830_g(g_grcRenderObjects, g_grcTextureParameter,
                                   reinterpret_cast<void*>(static_cast<uintptr_t>(texture)));
                textureDirty = g_grmShaderFx_forceResetFlag;
            }
        }
    }

    auto* pending = g_grmShaderFx_variantTable;
    auto* applied = g_grcAppliedRenderState;
    const auto setState = [](uint32_t offset, uint32_t value) {
        void* device = g_pGrcDeviceObj;
        using SetStateFn = void (*)(void*, uint32_t);
        auto fn = *reinterpret_cast<SetStateFn*>(static_cast<uint8_t*>(device) + offset);
        fn(device, value);
    };

    if ((g_grmShaderFx_flushRequired & 0x40000u) != 0) {
        const uint32_t firstUnused = pending[18];
        applied[18] = firstUnused;
        if (static_cast<int32_t>(firstUnused) < 8) {
            uint32_t offset = (firstUnused + 3176u) * 4u;
            do {
                auto* device = static_cast<uint8_t*>(g_pGrcDeviceObj);
                auto* binding = reinterpret_cast<uint32_t*>(device + offset);
                auto* texture = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(*binding));
                *binding = 0;
                if (texture != nullptr) {
                    const uint32_t references = texture[0] - 0x80000u;
                    texture[1] = *reinterpret_cast<uint32_t*>(device + 10396);
                    texture[0] = references;
                    if ((references & 0x00F800FFu) == 0) {
                        grcTexture_ReleaseResource(texture);
                    }
                }
                offset += 4;
            } while (static_cast<int32_t>(offset) < 12736);
        }
    }
    if ((g_grmShaderFx_flushRequired & 0x8100u) != 0) {
        applied[8] = pending[8];
        applied[15] = pending[15];
    }
    if ((g_grmShaderFx_flushRequired & 1u) != 0) {
        applied[0] = pending[0];
        setState(152, g_grcCullModeTable[pending[0]]);
    }
    if ((g_grmShaderFx_flushRequired & 0x200u) != 0) {
        applied[9] = pending[9];
        setState(308, g_grcColorWriteMaskTable[pending[9]]);
    }
    if ((g_grmShaderFx_flushRequired & 0x1000u) != 0) {
        applied[12] = pending[12];
        setState(408, pending[12]);
        applied[12] = pending[12];
        setState(156, pending[12]);
    }
    if ((g_grmShaderFx_flushRequired & 0x400u) != 0) {
        applied[10] = pending[10];
        setState(192, pending[10]);
    }
    if ((g_grmShaderFx_flushRequired & 8u) != 0) {
        setState(176, 0);
        const uint32_t blend = pending[3];
        applied[3] = blend;
        if ((blend & 0x4000u) != 0) {
            const uint32_t factors = blend & ~0x4000u;
            setState(168, factors & 0xFFFFu);
            setState(172, factors >> 16);
        } else if (blend <= 11) {
            static const uint8_t sourceBlend[12] = {6, 1, 1, 7, 10, 1, 10, 6, 1, 1, 1, 6};
            static const uint8_t destBlend[12] = {7, 1, 1, 6, 1, 0, 11, 1, 1, 1, 1, 1};
            setState(168, sourceBlend[blend]);
            setState(172, destBlend[blend]);
            switch (blend) {
            case 2: setState(176, 1); break;
            case 8: case 11: setState(176, 4); break;
            case 9: setState(176, 2); break;
            case 10: setState(176, 3); break;
            }
        }
    }
    if ((g_grmShaderFx_flushRequired & 0x10u) != 0) {
        applied[4] = pending[4];
        setState(200, g_grcCompareFuncTable[pending[4]]);
    }
    if ((g_grmShaderFx_flushRequired & 0x10000u) != 0) {
        applied[16] = pending[16];
        setState(148, g_grcFillModeTable[pending[16]]);
    }
    if ((g_grmShaderFx_flushRequired & 0x20u) != 0) {
        applied[5] = pending[5];
        setState(196, pending[5]);
    }
    if ((g_grmShaderFx_flushRequired & 0x40u) != 0) {
        const uint32_t value = pending[6];
        applied[6] = value;
        setState(140, g_grcFormatId == 0x1A220197u ? g_grcFormatCompareTable[value]
                                                : g_grcCompareFuncTable[value]);
    }
    if ((g_grmShaderFx_flushRequired & 0x80000u) != 0) {
        applied[19] = pending[19];
        setState(136, pending[19]);
    }
    if ((g_grmShaderFx_flushRequired & 0x80u) != 0) {
        applied[7] = pending[7];
        setState(144, pending[7]);
    }
    g_grmShaderFx_flushRequired = 0;
    g_grmShaderFx_forceResetFlag = 0;
}

extern "C" {
extern void grc_89D0(void* texture, uint32_t slice, uint32_t level, uint32_t* pitch,
                     uint32_t* size, uint32_t* offset, uint32_t* packedSize, uint32_t* width,
                     uint32_t* height, uint32_t* depth, uint32_t* address);  // @ 0x823589D0
extern void grcDevice_SetDepthStencilClear(void* device, uint32_t unusedR4,
    uint32_t unusedR5, uint32_t stencil, float depth); // @ 0x8235D700
// The color arrives in v1 on Xenon, independently of r3..r6.
extern void fiAsciiTokenizer_D808_fw(uint32_t format, uint32_t numberFormat,
                                    uint32_t* low, uint32_t* high);  // @ 0x8235D808
extern void game_37B0(void* device, int32_t left, int32_t top,
                      int32_t right, int32_t bottom);  // @ 0x823537B0
extern void grc_3E20(void* device);  // @ 0x82363E20
extern uint32_t* grc_DBF8(void* device, uint32_t* cursor);  // @ 0x8235DBF8
extern float* grc_A088(void* device, uint32_t count, uint32_t stride);  // @ 0x8235A088
extern void grc_CFD8(void* device, uint32_t flags, const int32_t* rect, const float* color,
                     float depth, uint32_t stencil);  // @ 0x8235CFD8
extern void rage_AD98(void* device);  // @ 0x8235AD98
extern void grcDevice_FlushDirtyState(void* device);  // @ 0x82363C00
extern uint32_t* grc_9B60(void* fixups);  // @ 0x82359B60 — grow the draw-fixup list
}
extern const float g_grcResolveConstants[];  // @ 0x8202D10C
extern const uint16_t g_grcResolveFormatInfo[64];  // @ 0x82065C68
extern const int32_t g_grcResolveOrigin[2];  // @ 0x82065E50
extern const uint32_t g_grcResolveVertexProgram[15];  // @ 0x8202C12C
extern const uint32_t g_grcResolveViewport[6];  // @ 0x82065CE8
extern const uint32_t g_grcResolveScissor[4];  // @ 0x82065D00
extern uint32_t g_grcResolveDisableWait;  // @ 0x82606640
extern uint32_t g_grcResolveForceShaderControl;  // @ 0x82606644
extern uint32_t g_grcResolveExtraWaits;  // @ 0x82606648
extern uint32_t g_grcResolveSubmit;  // @ 0x8260664C
extern uint32_t g_grcResolveSkipShaderControl;  // @ 0x82606650

// Begin a draw from caller-filled vertex memory. Returns the 16-byte-aligned
// allocation, or null on allocation failure; the caller fills it before submission.
// Xenon r3..r6: device, primitive type, vertex count, vertex stride in bytes.
// +13652/+13656/+13664 save the packet end, vertex address and allocation word count.
// The command cursor is the last written word, and is published here only on failure.
// @ 0x82357630
extern "C" void* grcDevice_BeginDrawPrimitiveUP(void* device, uint32_t primitiveType,
                                               uint32_t vertexCount, uint32_t vertexStride) {
    auto* state = static_cast<uint8_t*>(device);
    auto word = [state](uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(state + offset);
    };
    auto dirty = [state](uint32_t offset) -> uint64_t& {
        return *reinterpret_cast<uint64_t*>(state + offset);
    };
    auto pointer = [](uint32_t address) -> uint32_t* {
        return reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(address));
    };
    auto address = [](const void* p) {
        return static_cast<uint32_t>(reinterpret_cast<uintptr_t>(p));
    };
    auto physical = [](uint32_t value) {
        return (value & 0x1FFFFFFFu) + ((((value >> 20) + 512u) & 0x1000u));
    };
    const uint32_t vertexWords = (vertexCount * vertexStride) >> 2;
    if (word(11540) != 0) {
        word(11540) = 0;
        dirty(40) |= UINT64_C(0x2000000000000000);
    }
    const uint8_t savedStride = state[12688];
    const uint32_t strideWords = vertexStride >> 2;
    state[12688] = static_cast<uint8_t>(strideWords);
    if (strideWords != state[11424]) {
        dirty(48) |= 0x80u;
    }
    dirty(48) &= ~UINT64_C(0x400);
    grcDevice_FlushDirtyState(device);
    state[12688] = savedStride;
    dirty(48) |= 0x400u;

    uint32_t* cursor = pointer(word(0));
    if (word(0) > word(8)) {
        cursor = static_cast<uint32_t*>(rage_A980(device));
    }
    void* vertices = grc_A088(device, vertexWords, 16);
    if (vertices == nullptr) {
        word(0) = address(cursor);
        return nullptr;
    }
    auto emit = [&cursor](uint32_t value) { *++cursor = value; };
    // Six fetch constants, then a three-word zero register run.
    emit(0x000548BA); emit(1); emit(0); emit(1); emit(0);
    emit(physical(address(vertices)) | 3u);
    emit(0x10000002u | ((vertexWords << 2) & 0x03FFFFFCu));
    emit(0x00025000); emit(0); emit(0); emit(0);

    const uint32_t selector = state[12299];
    const uint32_t drawState = (state[12234 + selector] | (selector != 0 ? 0x100u : 0u)) & ~0xC0u;
    const uint32_t draw = (primitiveType & 0x3Fu) | (vertexCount << 16) | 0x80u;
    if ((state[10432] & 4u) == 0) {
        emit(0xC0012201); emit(drawState); emit(draw);
    } else {
        // Record the draw's packet cursor plus three fixup placeholders. This
        // path surrounds the draw with bin masks and emits the fixup/event words.
        uint32_t* fixup = pointer(word(13560));
        if (word(13560) + 16u > word(13564)) {
            fixup = grc_9B60(state + 13552);
        }
        fixup[0] = address(cursor);
        fixup[1] = 0xF00D; fixup[2] = 0xF00D; fixup[3] = 0xF00D;
        word(13560) = address(fixup) + 16u;
        emit(0xC0015000); emit(0xFFFFFFFF); emit(0);
        emit(0xC0012201); emit(drawState); emit(draw);
        emit(0xC0015000); emit(0x80000000); emit(0);
        emit(0xC0015A01); emit(26);
        emit(physical(address(fixup + 1) & ~1u) | 1u);
        emit(0xC0004601); emit(25);
    }
    word(13652) = address(cursor);
    word(13656) = address(vertices);
    word(13664) = vertexWords;
    return vertices;
}

// Resolve an EDRAM color/depth target into a texture, optionally clearing the source.
// Xenon: r3..r10 are the first eight arguments, depth is in f1, stencil at caller +0x5C.
// Destination level (r8) and resolve parameters (caller +0x64) are unused by this implementation.
// slice selects a destination subresource.
// @ 0x8235DD08
extern "C" void grcDevice_Resolve(void* device, uint32_t flags, const int32_t* sourceRect,
                                   void* texture, const int32_t* destinationPoint, uint32_t /*destinationLevel*/,
                                   uint32_t slice, const float* clearColor, float clearDepth,
                                   uint32_t clearStencil, const void* /*resolveParameters*/) {
    uint8_t* state = static_cast<uint8_t*>(device);
    auto word = [state](uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(state + offset);
    };
    auto dirty = [state](uint32_t offset) -> uint64_t& {
        return *reinterpret_cast<uint64_t*>(state + offset);
    };
    auto pointer = [](uint32_t address) -> uint32_t* {
        return reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(address));
    };
    auto available = [&]() -> uint32_t* {
        uint32_t* cursor = pointer(word(0));
        if (word(0) > word(8)) {
            cursor = static_cast<uint32_t*>(rage_A980(device));
        }
        return cursor;
    };
    auto saveCursor = [&](uint32_t* cursor) {
        word(0) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(cursor));
    };
    auto physical = [](uint32_t address) {
        return (address & 0x1FFFFFFFu) + ((((address >> 20) + 512u) & 0x1000u));
    };
    auto signed15 = [](uint32_t value) {
        return static_cast<int32_t>(value << 17) >> 17;
    };
    uint32_t* header = static_cast<uint32_t*>(texture);
    const uint32_t target = flags & 7u;
    if ((flags & 0x70u) == 0) {
        const uint32_t surface = word(target == 4 ? 12552 : (target + 3134u) * 4u);
        const uint32_t samples = *reinterpret_cast<const uint16_t*>(
            reinterpret_cast<const uint8_t*>(pointer(surface)) + 48) & 3u;
        flags |= samples == 0 ? 0x10u : samples == 1 ? 0x50u : 0x70u;
    }
    alignas(16) float defaultColor[4] = {
        g_grcResolveConstants[1], g_grcResolveConstants[1],
        g_grcResolveConstants[1], g_grcResolveConstants[1]
    };
    if (!clearColor) {
        clearColor = defaultColor;
    }
    const bool volume = (header[9] & 0x600u) == 0x400u;
    const uint32_t dimensionBias = ((header[7] >> 30) & 2u) + 1u;
    uint32_t width = (header[6] & (volume ? 0x7FFu : 0x1FFFu)) + dimensionBias;
    uint32_t height = ((header[6] >> (volume ? 11 : 13)) & (volume ? 0x7FFu : 0x1FFFu)) + dimensionBias;
    uint32_t pitch = (header[4] >> 17) & 0x3FE0u;
    uint32_t base = header[5] & 0xFFFFF000u;
    const uint32_t bytesPerBlock = (g_grcResolveFormatInfo[header[5] & 63u] >> 3) & 31u;
    uint32_t unusedSize, unusedOffset, unusedPackedSize, unusedDepth;
    if (slice != 0) {
        uint32_t pitchBytes;
        grc_89D0(texture, slice, 0, &pitchBytes, &unusedSize, &unusedOffset,
                 &unusedPackedSize, &width, &height, &unusedDepth, &base);
        if (bytesPerBlock == 0) {
            __builtin_trap();
        }
        pitch = pitchBytes / bytesPerBlock;
    }
    int32_t defaultRect[4] = {0, 0, static_cast<int32_t>(width), static_cast<int32_t>(height)};
    if (!sourceRect) {
        sourceRect = defaultRect;
    }
    if (!destinationPoint) {
        destinationPoint = g_grcResolveOrigin;
    }
    const uint32_t destinationHeight = height - static_cast<uint32_t>(destinationPoint[1]);
    const uint32_t destination = physical(base)
        + ((static_cast<uint32_t>(destinationPoint[1]) - static_cast<uint32_t>(sourceRect[1])) * pitch
            + ((static_cast<uint32_t>(destinationPoint[0]) - static_cast<uint32_t>(sourceRect[0])) << 5))
           * bytesPerBlock;

    const bool forcedControl = g_grcResolveForceShaderControl != 0;
    if (forcedControl) {
        word(10400) |= 0x100u;
        uint32_t* cursor = available();
        *++cursor = 1480; *++cursor = 0x20000; *++cursor = 3841; *++cursor = word(10400);
        saveCursor(cursor);
    }
    uint32_t deferredClear = 0;
    if ((word(10400) & 0x100u) != 0
        && ((*reinterpret_cast<uint16_t*>(state + 11456) & 3u) != 2 || (flags & 0x70u) != 0x70u)) {
        deferredClear = flags & 0x300u;
        flags &= ~0x300u;
    }
    uint32_t format = header[5] & 63u;
    switch (format) {
    case 54: format = 7; break;
    case 55: format = 16; break;
    case 56: format = 17; break;
    case 27: format = 30; break;
    case 28: format = 31; break;
    case 29: format = 32; break;
    case 22: case 23: format = 6; break;
    }
    const uint32_t endian = (header[4] >> 2) & 3u;
    uint32_t numberFormat = (endian == 1 ? 1u : 0u) + ((header[7] & 1u) ? 2u : 0u);
    if (format == 30 || format == 31 || format == 32 || format == 36 || format == 37
        || format == 38 || format == 57 || format == 63) {
        numberFormat = 7;
    }
    const uint32_t copyFlags = ((flags >> 26) & 63u) | ((header[7] & 14u) ? 0x100u : 0u);
    uint32_t destinationInfo = (((((copyFlags & 319u) << 3) | numberFormat) << 6) | format) << 7;
    destinationInfo |= (header[5] >> 6) & 3u;
    if (volume) {
        word(11908) = pitch * height;
        destinationInfo |= ((slice << 4) & 0x70u) | 8u;
        dirty(48) |= 0x10000000u;
    }
    const uint32_t copyMode = (flags & 0x2000u) ? 3u : target == 4 ? 0u : 1u;
    const uint32_t copyControl = (copyMode << 20) | ((flags & 887u) - 16u);
    word(11876) = destinationInfo;
    word(11868) = destination;
    word(11872) = ((destinationHeight << 16) & 0x3FFF0000u) | (pitch & 0x3FFFu);
    word(11864) = copyControl;
    dirty(48) |= UINT64_C(0xF000000000);
    const bool clearDepthEnabled = (flags & 0x200u) != 0;
    if (clearDepthEnabled) {
        grcDevice_SetDepthStencilClear(device, 0, 0, clearStencil, clearDepth);
    }
    if ((flags & 0x100u) != 0) {
        const uint32_t colorTarget = copyControl & 7u;
        const uint32_t colorInfo = word(colorTarget == 0 ? 11460 : (colorTarget + 2866u) * 4u);
        uint32_t low, high;
#if defined(__powerpc__) || defined(__ppc__)
        // lvx deliberately rounds down to 16 bytes, as the original lvx128 does.
        __asm__ volatile("lvx 1, 0, %0" : : "r"(clearColor) : "v1", "memory");
#endif
        fiAsciiTokenizer_D808_fw((colorInfo >> 16) & 15u, (colorInfo >> 20) & 63u, &low, &high);
        word(11888) = low;
        word(11892) = high;
        dirty(48) |= UINT64_C(0x300000000);
    }

    const int32_t left = sourceRect[0], top = sourceRect[1];
    const int32_t right = static_cast<int32_t>((static_cast<uint32_t>(sourceRect[2]) + 7u) & ~7u);
    const int32_t bottom = static_cast<int32_t>((static_cast<uint32_t>(sourceRect[3]) + 7u) & ~7u);
    const bool expandScissor = left < signed15(word(11524)) || top < signed15(word(11524) >> 16)
        || right > signed15(word(11528)) || bottom > signed15(word(11528) >> 16);
    if (expandScissor) {
        game_37B0(device, left, top, right, bottom);
    }
    grc_3E20(device);
    bool tiledTargets = (state[10432] & 16u) != 0;
    for (uint32_t i = 0; i < 5 && tiledTargets; ++i) {
        tiledTargets = word(12536 + i * 4) == 0 || word(12536 + i * 4) == word(12976 + i * 4);
    }
    if (tiledTargets) {
        for (uint32_t i = 0; i < word(12996); ++i) {
            const uint32_t address = destination
                + (word(13244 + i * 16) * pitch + (word(13240 + i * 16) << 5)) * bytesPerBlock;
            uint32_t* cursor = available();
            const uint32_t shift = (i * 2u) & 63u;
            *++cursor = 0xC0015000; *++cursor = shift < 32 ? 3u << shift : 0;
            *++cursor = 0; *++cursor = 0xC0012D01; *++cursor = 0x40319; *++cursor = address;
            saveCursor(cursor);
        }
        uint32_t* cursor = available();
        *++cursor = 0xC0015000; *++cursor = word(12960) ? word(12960) : UINT32_MAX; *++cursor = 0;
        saveCursor(cursor);
    }
    uint32_t* cursor = available();
    if ((state[10434] & 32u) != 0 && g_grcResolveDisableWait == 0) {
        for (int i = 0; i < 3; ++i) {
            *++cursor = 0xC0004600; *++cursor = 6;
        }
        state[10434] &= ~32u;
    }
    *++cursor = 0xC0102B00; *++cursor = 0; *++cursor = 15;
    for (uint32_t value : g_grcResolveVertexProgram) {
        *++cursor = value;
    }
    *++cursor = 0x12180; *++cursor = 0x10002; *++cursor = 0;
    *++cursor = 8712; *++cursor = 6; *++cursor = 8704; *++cursor = 0;
    uint32_t depthControl = 0;
    if (clearDepthEnabled) {
        const uint32_t savedFlags = state[10434];
        depthControl = (word(11648) & ~15u) | (savedFlags >> 7) | ((savedFlags >> 5) & 4u);
        state[10433] |= 8u;
        dirty(48) |= 32u;
    }
    *++cursor = 8707; *++cursor = depthControl;
    if (g_grcResolveSkipShaderControl == 0) {
        *++cursor = 1480; *++cursor = 0x20000;
    }
    saveCursor(cursor);
    if (reinterpret_cast<uintptr_t>(cursor) > word(8)) {
        cursor = static_cast<uint32_t*>(rage_A980(device));
    }
    cursor = grc_DBF8(device, cursor);
    saveCursor(cursor);
    if (endian == 3 && target != 4) {
        const uint32_t index = target == 0 ? 0 : target + 1;
        const uint32_t colorInfo = word((index + 2865u) * 4u);
        if ((colorInfo & 0xF0000u) == 0x10000u) {
            cursor = available();
            *++cursor = index + 8193u;
            *++cursor = colorInfo & 0x3F00FFFu;
            const uint32_t registerIndex = index + 0x20123u;
            const uint32_t shift = registerIndex & 127u;
            dirty(16 + (registerIndex >> 16) * 8) |= shift < 64 ? UINT64_C(0x8000000000000000) >> shift : 0;
            saveCursor(cursor);
        }
    }
    cursor = available();
    float* vertices = grc_A088(device, 6, 4);
    if (!vertices) {
        saveCursor(cursor);
        return;
    }
    const uint32_t vertexAddress = physical(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(vertices)));
    const float pixelOffset = (word(11776) & 1u) ? g_grcResolveConstants[1] : g_grcResolveConstants[0];
    const float x = static_cast<float>(left) - pixelOffset;
    const float y = static_cast<float>(top) - pixelOffset;
    vertices[0] = x; vertices[2] = x; vertices[3] = y; vertices[5] = y;
    vertices[4] = static_cast<float>(static_cast<int32_t>(static_cast<uint32_t>(right) - left)) + x;
    vertices[1] = static_cast<float>(static_cast<int32_t>(static_cast<uint32_t>(bottom) - top)) + y;
    *++cursor = 0x54800; *++cursor = vertexAddress | 3u; *++cursor = 0x1000001A;
    *++cursor = 0; *++cursor = 0; *++cursor = 0; *++cursor = 0;
    *++cursor = 0x25000; *++cursor = 0; *++cursor = 0; *++cursor = 0;
    *++cursor = 0xC0003601; *++cursor = 0x30088;
    saveCursor(cursor);
    cursor = available();
    if (g_grcResolveDisableWait == 0) {
        *++cursor = 0xC0004600; *++cursor = 6;
    }
    if (g_grcResolveExtraWaits != 0) {
        for (int i = 0; i < 8; ++i) {
            *++cursor = 0xC0004600; *++cursor = 6;
        }
    }
    *++cursor = 8199; *++cursor = word(11484);
    saveCursor(cursor);
    if (expandScissor) {
        game_37B0(device, signed15(word(11524)), signed15(word(11524) >> 16),
                   signed15(word(11528)), signed15(word(11528) >> 16));
    }
    const uint32_t resolveBytes = destinationHeight * pitch * bytesPerBlock;
    header[1] = word(10396);
    dirty(48) |= 128u;
    dirty(40) |= UINT64_C(0x62420000000);
    dirty(32) |= UINT64_C(0x8000000000000000);
    cursor = available();
    *++cursor = 2609; *++cursor = 0x3000100; *++cursor = 0x10A2F;
    *++cursor = (resolveBytes + 8191u) & ~0xFFFu; *++cursor = destination & ~0xFFFu;
    *++cursor = 0xC0043C00; *++cursor = 3; *++cursor = 2609; *++cursor = 0;
    *++cursor = 0x80000000; *++cursor = 8;
    word(11864) = 0;
    word(11876) = 0;
    *++cursor = 8984; *++cursor = 0; *++cursor = 8987; *++cursor = 0;
    saveCursor(cursor);
    header[1] = word(10396);
    if (deferredClear != 0) {
        const uint32_t clearFlags = ((deferredClear & 0x200u) ? 48u : 0u)
            | ((deferredClear & 0x100u) ? 1u << target : 0u);
        uint32_t savedViewport[6], savedScissor[4];
        for (uint32_t i = 0; i < 6; ++i) savedViewport[i] = word(12808 + i * 4);
        for (uint32_t i = 0; i < 4; ++i) savedScissor[i] = word(12832 + i * 4);
        grcDevice_SetViewport(device, g_grcResolveViewport);
        grc_5E08(device, g_grcResolveScissor);
        grc_CFD8(device, clearFlags, sourceRect, clearColor, clearDepth, clearStencil);
        grcDevice_SetViewport(device, savedViewport);
        grc_5E08(device, savedScissor);
    }
    if (forcedControl) {
        cursor = available();
        word(10400) &= ~0x100u;
        *++cursor = 1480; *++cursor = 0x20000; *++cursor = 3841; *++cursor = word(10400);
        saveCursor(cursor);
    }
    if (g_grcResolveSubmit != 0) {
        rage_AD98(device);
    }
}

// Former auto-name CCalMoviePlayer_D700_p39. Pack D24S8 or float24 depth and
// update clear registers, preserving every unrelated dirty-state bit.
// Explicit unused GPRs keep stencil in Xenon's r6 as well as ppc32's r6.
// @ 0x8235D700 | size: 0x104 (includes four padding bytes)
extern "C" void grcDevice_SetDepthStencilClear(void* device, uint32_t unusedR4,
    uint32_t unusedR5, uint32_t stencil, float depth) {
    (void)unusedR4; (void)unusedR5;
    auto* dev = static_cast<uint8_t*>(device);
    uint32_t packed, mode;
    if ((*reinterpret_cast<uint16_t*>(dev + 11464) & 1) == 0) {
        // fctidz saturates to signed 64 bits; stfiwx keeps the low word.
        auto convert = [](float value) -> uint32_t {
            if (!(value >= -0x1p63f)) return 0;
            if (value >= 0x1p63f) return 0xFFFFFFFFu;
            return static_cast<uint32_t>(static_cast<int64_t>(value));
        };
        packed = (convert(depth * 16777215.0f) << 8) | stencil;
        mode = convert(depth * 2047.0f);
    } else {
        uint32_t bits;
        __builtin_memcpy(&bits, &depth, 4);
        uint32_t value;
        if (bits & 0x80000000u) {
            value = 0;
        } else {
            const unsigned exponent = bits >> 23;
            if (exponent >= 113) {
                value = ((bits & 0x07800000u) | (bits + 4)) >> 3;
            } else {
                const unsigned shift = 113 - exponent;
                // Xenon's slw/srw use six shift bits; bit 5 zeroes the result.
                const unsigned roundShift = (shift - 1) & 63;
                const uint32_t round = roundShift < 32 ? 1u << roundShift : 0;
                const uint32_t mantissa = ((bits & 0x7FFFFFu) + round) | 0x800000u;
                const unsigned resultShift = shift & 63;
                value = resultShift < 32 ? mantissa >> resultShift : 0;
            }
        }
        packed = (value << 8) | (stencil & 0xFF);
        mode = packed >> 21;
    }
    const uint32_t state = *reinterpret_cast<uint32_t*>(dev + 11648);
    const uint32_t sameStencil = stencil == dev[11650] ? 0x800 : 0;
    *reinterpret_cast<uint32_t*>(dev + 11884) = packed;
    *reinterpret_cast<uint32_t*>(dev + 11880) = mode | ((sameStencil ^ 0x800) ^ ((~state << 6) & 0x800));
    *reinterpret_cast<uint64_t*>(dev + 48) |= 3ULL << 34;
}
