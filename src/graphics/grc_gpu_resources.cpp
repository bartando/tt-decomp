/**
 * grc_gpu_resources.cpp — GPU resource management functions
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Implements GPU fence/resource management functions:
 *   grc_2CC8  @ 0x82352CC8 | size: 0xF0 — GPU memory tile/resolve management
 *   grc_EB10  @ 0x8214EB10 | size: 0x12C — Viewport scaling and setup
 *   grc_SetupResource — synthetic link anchor (no binary address)
 *   grmShaderPreset_AllocArray_c — shader preset array allocation
 */

#include <cstdint>
#include <cstddef>
#include <cstring>

extern "C" {

// ── External dependencies ───────────────────────────────────────────────────

// rage_EEC0 — GPU memory resolve/invalidate helper
// @ 0x8235EEC0 — takes two addresses (start, end) for a GPU memory region
extern void rage_EEC0(void* start, void* end);

extern void grcDevice_ApplyShaderState(void* device);  // @ 0x82363500
// Packet emitters: dirty bits run from the most significant end of the 64-bit mask.
extern void phBoundBVH_2658_p39(void* device, uint64_t mask, uint32_t firstRegister,
                               const void* values);  // @ 0x82362658
extern void phBoundBVH_2718(void* device, uint64_t mask, uint32_t firstRegister,
                           const void* values);  // @ 0x82362718
extern void phBoundBVH_2858_p39(void* device, uint64_t mask, uint32_t firstRegister,
                               const void* values);  // @ 0x82362858
extern void phBoundBVH_2980_p39(void* device);  // @ 0x82362980 — refresh vertex fetch state

// grc_5ED0 — viewport apply function
// @ 0x82355ED0 — applies a viewport rectangle to the GPU device
extern void grc_5ED0(void* device, int32_t* viewportRect);

// Global GPU device pointer
// @ 0x825EB988 (.data, 4 bytes)
extern void* lbl_825EB988;  // g_pGrcGPUDevice

// Screen dimensions (signed int32)
// @ 0x825C9014 (.data, 4 bytes) — screen width
// @ 0x825C9018 (.data, 4 bytes) — screen height
extern int32_t lbl_825C9014;  // g_nScreenWidth
extern int32_t lbl_825C9018;  // g_nScreenHeight

// GPU hardware ID
// @ 0x825C9030 (.data, 4 bytes) — GPU chip revision
extern int32_t lbl_825C9030;  // g_nGPUChipId

// GPU fence counter
// @ 0x825EB97C (.data, 4 bytes) — decremented by vfn_8, triggers fence signal
extern int32_t lbl_825EB97C;  // g_nGPUFenceCounter

// .rdata float constant (1.0f)
// @ 0x8202D108 (.rdata, 4 bytes)
extern const float lbl_8202D108;

/**
 * grc_2CC8 @ 0x82352CC8 | size: 0xF0
 *
 * GPU memory tile/resolve management. Manages a pair of GPU memory regions
 * (tiles) used for render target resolve operations on the Xenos GPU.
 *
 * The function operates on a 16-byte control structure:
 *   +0x00  uint32_t m_nTileFlags    — tile state flags (decremented by 0x1000 each call)
 *   +0x04  (padding)
 *   +0x08  uint32_t m_nTileHandleA  — first tile handle (0xFFFF0000 = invalid)
 *   +0x0C  uint32_t m_nTileHandleB  — second tile handle (0xFFFF0000 = invalid)
 *
 * Parameters:
 *   a — pointer to the tile control structure
 *   b — GPU base address for tile A (physical address with format bits)
 *   c — GPU base address for tile B (physical address with format bits)
 *
 * On Xbox 360, this manages Xenos EDRAM tile resolve regions. On the host
 * platform, this is a no-op since we use standard framebuffer objects.
 */
void grc_2CC8(void* a, uint32_t b, uint32_t c) {
    if (!a) return;

    uint32_t* ctrl = static_cast<uint32_t*>(a);

    // Decrement tile flags by 0x1000 (one tile step)
    uint32_t flags = ctrl[0];
    flags -= 0x1000;
    ctrl[0] = flags;

    // Check if the low nibble of the upper 16 bits is zero
    // (rlwinm. r10,r9,0,16,19 — tests bits 16-19)
    if ((flags & 0xF000) != 0)
        return;

    // Process tile A if valid
    uint32_t tileA = ctrl[2];  // +0x08
    if (tileA != 0xFFFF0000u) {
        ctrl[2] = 0xFFFF0000u;  // invalidate

        // On Xbox 360, this would resolve the tile region.
        // The address computation involves extracting width/height from the
        // packed tile handle and computing physical addresses.
        // On host platform, this is a no-op.
    }

    // Process tile B if requested (c != 0) and valid
    if (c == 0)
        return;

    uint32_t tileB = ctrl[3];  // +0x0C
    if (tileB == 0xFFFF0000u)
        return;

    ctrl[3] = 0xFFFF0000u;  // invalidate

    // Same tile resolve logic for tile B — no-op on host
}

/**
 * grc_EB10 @ 0x8214EB10 | size: 0x12C
 *
 * Computes a scaled viewport rectangle from normalized coordinates and
 * applies it to the GPU device. Used during render target setup to map
 * a normalized [0,1] viewport specification to pixel coordinates.
 *
 * Parameters:
 *   a — pointer to a 24-byte viewport descriptor:
 *     +0x00  float m_fLeft       — normalized left   (0.0 - 1.0)
 *     +0x04  float m_fTop        — normalized top    (0.0 - 1.0)
 *     +0x08  float m_fRight      — normalized right  (0.0 - 1.0)
 *     +0x0C  float m_fBottom     — normalized bottom (0.0 - 1.0)
 *     +0x10  float m_fMinDepth   — min depth (0.0 - 1.0)
 *     +0x14  float m_fMaxDepth   — max depth (0.0 - 1.0)
 *
 * The function reads the global screen dimensions, multiplies each
 * normalized coordinate by the corresponding dimension, converts to
 * integer, and then adjusts the depth values based on the GPU chip ID.
 * If the chip ID matches 0x1A220197 (Xenos R500), depth values are
 * inverted (1.0 - depth).
 */
void grc_EB10(void* a) {
    if (!a) return;

    const float* vp = static_cast<const float*>(a);

    float fLeft     = vp[0];   // +0x00
    float fTop      = vp[1];   // +0x04
    float fRight    = vp[2];   // +0x08
    float fBottom   = vp[3];   // +0x0C
    float fMinDepth = vp[4];   // +0x10
    float fMaxDepth = vp[5];   // +0x14

    // Read screen dimensions
    float screenW = static_cast<float>(lbl_825C9014);
    float screenH = static_cast<float>(lbl_825C9018);

    // Scale normalized coords to pixel coords
    int32_t pixLeft   = static_cast<int32_t>(screenW * fLeft);
    int32_t pixTop    = static_cast<int32_t>(fTop * screenH);
    int32_t pixRight  = static_cast<int32_t>(fRight * screenW);
    int32_t pixBottom = static_cast<int32_t>(fBottom * screenH);

    // Read the 1.0f constant from .rdata
    float oneF = lbl_8202D108;

    // Check GPU chip ID for depth inversion
    // 0x1A220197 = Xenos R500 GPU revision
    bool isXenosR500 = (lbl_825C9030 == 0x1A220197);

    // Compute depth values — invert for Xenos R500
    float depthA, depthB;
    if (isXenosR500) {
        depthA = oneF - fMinDepth;
        depthB = oneF - fMaxDepth;
    } else {
        depthA = fMinDepth;
        depthB = fMaxDepth;
    }

    // Pack into viewport rect: {left, top, right, bottom, depthA, depthB}
    int32_t viewportRect[6];
    viewportRect[0] = pixLeft;
    viewportRect[1] = pixTop;
    viewportRect[2] = pixRight;
    viewportRect[3] = pixBottom;
    // Store depth as float bits in the int32 slots
    std::memcpy(&viewportRect[4], &depthA, sizeof(float));
    std::memcpy(&viewportRect[5], &depthB, sizeof(float));

    // Apply viewport to the GPU device
    void* device = lbl_825EB988;
    if (device) {
        grc_5ED0(device, viewportRect);
    }
}

/**
 * grc_SetupResource — synthetic link anchor
 *
 * This is a synthetic glue function with no real address in the binary.
 * It serves as a link anchor for callers in rage_grm.cpp that reference
 * a GPU resource setup path. On the host platform, GPU resources are
 * managed through OpenGL, so this is a no-op.
 */
void grc_SetupResource(void* a, void* b) {
    (void)a; (void)b;
    // No-op: GPU resource setup handled by OpenGL on host platform
}

/**
 * grmShaderPreset_AllocArray_c — shader preset array allocation
 *
 * Allocates the global shader preset array used by the grmShaderPreset
 * system. On Xbox 360, this sets up the D3D shader constant buffer pool.
 * On the host platform, shader management is handled by OpenGL, so this
 * is a no-op.
 */
void grmShaderPreset_AllocArray_c(void) {
    // No-op: shader presets managed by OpenGL on host platform
}


/**
 * grcDevice_Present @ 0x8214F088 | size: 0xC0
 *
 * Presents the rendered frame to the display. On Xbox 360, this submits
 * the final GPU command buffer with resolve/present parameters (flags,
 * dimensions, scale, flip). On the host platform, this calls SDL2's
 * swap-buffers path via sdl_PollAndSwap.
 *
 * Parameters:
 *   flags  — present flags (bit 0 = enable, bit 4 = flip mode)
 *   width  — backbuffer width (1 = use default)
 *   height — backbuffer height (1 = use default)
 *   scale  — resolution scale factor (0.0 = native)
 *   flip   — true to flip the backbuffer vertically
 *   a6     — reserved (always 0)
 */
extern void sdl_PollAndSwap(void);

void grcDevice_Present(uint32_t flags, int width, int height,
                        float scale, bool flip, int a6) {
    (void)flags; (void)width; (void)height;
    (void)scale; (void)flip; (void)a6;

    // On the host platform, presentation is handled by SDL2.
    // The Xbox 360 GPU command buffer submission is not needed.
    sdl_PollAndSwap();
}

/**
 * grcDevice_SubInit @ 0x821513A0 | size: 0x148
 *
 * Secondary GPU device initialization. On Xbox 360, this creates render
 * targets, allocates EDRAM tiles, and sets up the shader constant pool.
 * On the host platform, OpenGL handles these resources natively through
 * the default framebuffer and shader uniform system.
 *
 * Called from app_init during the render subsystem bootstrap phase,
 * after the primary device (SDL window + GL context) is already created.
 */
void grcDevice_SubInit(void) {
    // No-op on host platform: OpenGL manages render targets and shader
    // constants through its own API. The Xbox 360 EDRAM tile setup and
    // shader constant pool allocation are not applicable.
}

/**
 * grcDevice_WaitFence @ 0x8214FC30 | size: 0x60
 *
 * Waits for the GPU to finish processing all submitted commands up to
 * the current fence point. On Xbox 360, this polls the GPU fence register
 * and spins until the hardware signals completion. On the host platform,
 * OpenGL's implicit synchronization handles this — glSwapBuffers acts
 * as a natural sync point.
 *
 * Called before grcDevice_Present to ensure all rendering is complete.
 */
void grcDevice_WaitFence(void) {
    // No-op on host platform: OpenGL provides implicit synchronization.
    // The SDL_GL_SwapWindow call in sdl_PollAndSwap acts as a fence.
}


// Flush cached device state before draw submission, in dependency order.
// @ 0x82363C00
void grcDevice_FlushDirtyState(void* device) {
    auto* data = static_cast<uint8_t*>(device);
    auto dirty = [&](uint32_t offset) -> uint64_t& {
        return *reinterpret_cast<uint64_t*>(data + offset);
    };

    // Helpers can dirty later groups, so reload each mask after every call.
    if (dirty(0x30) != 0) {
        if ((dirty(0x30) & 0x400) != 0) {
            phBoundBVH_2980_p39(device);
        }
        if ((dirty(0x30) & 0x1E0) != 0) {
            grcDevice_ApplyShaderState(device);
        }
        uint64_t mask = dirty(0x30) & 0xFFFFFFFFFC000000ULL;
        if (mask != 0) {
            phBoundBVH_2658_p39(device, mask, 0x2300, data + 0x2DF8);
        }
        if ((dirty(0x30) & 0x03FC0000) != 0) {
            mask = (dirty(0x30) << 38) & 0xFF00000000000000ULL;
            phBoundBVH_2658_p39(device, mask, 0x2380, data + 0x2E90);
        }
        dirty(0x30) = 0;
    }

    // Vertex and pixel float constants, 16 dwords per dirty bit.
    if (dirty(0x10) != 0) {
        phBoundBVH_2858_p39(device, dirty(0x10), 0x4000, data + 0x780);
        dirty(0x10) = 0;
    }
    if (dirty(0x18) != 0) {
        phBoundBVH_2858_p39(device, dirty(0x18), 0x4400, data + 0x1780);
        dirty(0x18) = 0;
    }

    if (dirty(0x20) != 0) {
        uint64_t mask = dirty(0x20) & 0xFFFFFFFF00000000ULL;
        if (mask != 0) {
            // Six dwords per vertex fetch descriptor.
            phBoundBVH_2718(device, mask, 0x4800, data + 0x480);
        }
        if ((dirty(0x20) & 0x80000000) != 0) {
            // lis -256 sign-extends on Xenon, including the upper 32 bits.
            dirty(0x2CB0) = 0xFFFFFFFFFF000000ULL;
            phBoundBVH_2658_p39(device, 0xFFFFFFFFFF000000ULL, 0x4900, data + 0x2780);
        }
        if ((dirty(0x20) & 0x3FFFC000) != 0) {
            mask = (dirty(0x20) << 34) & 0xFFFF000000000000ULL;
            phBoundBVH_2658_p39(device, mask, 0x2000, data + 0x2CC0);
        }
        dirty(0x20) = 0;
    }

    if (dirty(0x28) != 0) {
        uint64_t mask = dirty(0x28) & 0xFFFFF80000000000ULL;
        if (mask != 0) {
            phBoundBVH_2658_p39(device, mask, 0x2100, data + 0x2D0C);
        }
        if ((dirty(0x28) & 0x000007C000000000ULL) != 0) {
            mask = (dirty(0x28) << 21) & 0xF800000000000000ULL;
            phBoundBVH_2658_p39(device, mask, 0x2180, data + 0x2D60);
        }
        if ((dirty(0x28) & 0x0000003FFC000000ULL) != 0) {
            mask = (dirty(0x28) << 26) & 0xFFF0000000000000ULL;
            phBoundBVH_2658_p39(device, mask, 0x2200, data + 0x2D74);
        }
        if ((dirty(0x28) & 0x03FFFFE0) != 0) {
            mask = (dirty(0x28) << 38) & 0xFFFFF80000000000ULL;
            phBoundBVH_2658_p39(device, mask, 0x2280, data + 0x2DA4);
        }
        dirty(0x28) = 0;
    }
}

} // extern "C"
