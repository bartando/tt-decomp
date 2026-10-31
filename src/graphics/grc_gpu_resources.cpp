/**
 * grc_gpu_resources.cpp — GPU resource management functions
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Implements GPU fence/resource management functions:
 *   grc_2CC8  @ 0x82352CC8 | size: 0xF0 — GPU memory tile/resolve management
 *   grcSetNormalizedViewport  @ 0x8214EB10 | size: 0x12C — Viewport scaling and setup
 *   grcDevice_ApplyShaderState @ 0x82363500 — shader binding and dependent GPU state
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

extern void* rage_A980(void* device);  // @ 0x8235A980
extern void grcPatchVertexFetchInstructions(void* device, void* shader, uint32_t codeAddress, void* declaration);  // @ 0x82362A68
extern void rage_32F0(void* device, uint32_t repatch, void* shader, uint32_t* programControl,
                      void* declaration, const void* vertexInfo, const void* pixelInfo);  // @ 0x823632F0
extern void grc_3410(void* device);  // @ 0x82363410
extern uint32_t g_grcShaderPatchSerial;  // @ 0x8271A83C
extern void grcDevice_ApplyShaderState(void* device);  // @ 0x82363500
// Packet emitters: dirty bits run from the most significant end of the 64-bit mask.
void grcDevice_FlushDirtySixRegisterGroups(void* device, uint64_t dirty, uint32_t firstRegister,
                                           const uint32_t* values);  // defined below
void grcDevice_FlushDirtySixteenRegisterGroups(void* device, uint64_t dirty, uint32_t firstRegister,
                                              const uint32_t* values);  // defined below

extern "C" void grcDevice_SetViewport(void* device, const void* viewport);  // @ 0x82355ED0

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
 * grcSetNormalizedViewport @ 0x8214EB10 | size: 0x12C
 *
 * Computes a scaled viewport rectangle from normalized coordinates and
 * applies it to the GPU device. Used during render target setup to map
 * a normalized [0,1] viewport specification to pixel coordinates.
 *
 * Parameters:
 *   vp — pointer to a 24-byte viewport descriptor:
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
void grcSetNormalizedViewport(const float* vp) {

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
    grcDevice_SetViewport(device, viewportRect);
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


// Vertex declaration entries and shader fetch templates use the Xenon layouts.
struct grcVertexElement {
    uint16_t stream;
    uint16_t offset;
    uint32_t format;
    uint8_t method;
    uint8_t usage;
    uint8_t usageIndex;
    uint8_t reserved;
};
static_assert(sizeof(grcVertexElement) == 12);
struct grcFetchInstruction { uint32_t opcode, format, offset; };
struct grcVertexFetchShader {
    uint8_t reserved[0x34];
    uint32_t fetchCount;
    uint32_t fetchLocations[32]; // low 12 bits: instruction index; bits 20..23: boundary
    grcFetchInstruction fetchTemplates[32];
};
static_assert(offsetof(grcVertexFetchShader, fetchTemplates) == 0xB8);
struct grcVertexFetchDeclaration {
    uint8_t reserved[8];
    uint32_t elementCount;
    uint8_t state[0x18];
};
static_assert(sizeof(grcVertexFetchDeclaration) == 0x24);
extern const uint16_t g_grcFetchSwizzleMasks[8]; // @ 0x8202C318
extern const uint8_t g_grcFetchFormatSizes[64]; // @ 0x82065F68

static uint32_t rotateFetchWord(uint32_t value, unsigned shift) {
    return (value << shift) | (value >> (32 - shift));
}
static uint32_t fetchConstantIndex(uint32_t opcode) {
    return ((opcode >> 18) & 0x7C) | ((opcode >> 25) & 3);
}
static int32_t fetchOffset(uint32_t word) {
    return static_cast<int32_t>(word << 1) >> 9;
}

// Formerly rage_2A68. Patch fetch formats/streams, sort bounded fetch groups,
// and merge adjacent fetches into bursts before scattering into shader code.
// Scratch capacity matches the shader's 32-entry metadata arrays.
// @ 0x82362A68
void grcPatchVertexFetchInstructions(void* device, void* shader, uint32_t codeAddress, void* declaration) {
    const auto* input = static_cast<const grcVertexFetchShader*>(shader);
    const auto* layout = static_cast<const grcVertexFetchDeclaration*>(declaration);
    const auto* elements = reinterpret_cast<const grcVertexElement*>(layout + 1);
    const auto* strides = static_cast<const uint8_t*>(device) + 0x3190;
    grcFetchInstruction patched[32];
    const uint32_t count = input->fetchCount;
    for (uint32_t i = 0; i < count; ++i) {
        const uint32_t location = input->fetchLocations[i];
        const grcVertexElement* element = nullptr;
        for (uint32_t j = 0; j < layout->elementCount; ++j) {
            const auto& candidate = elements[j];
            if (candidate.usage == ((location >> 12) & 15) &&
                candidate.usageIndex == ((location >> 16) & 15)) {
                element = &candidate;
                break;
            }
        }
        auto instruction = input->fetchTemplates[i];
        uint32_t swizzle;
        if (!element) {
            instruction.opcode = (instruction.opcode & ~0x3FF00000u) | 0x05F00000u;
            instruction.format = (instruction.format & 0xBFC6CFFFu) | 0x60000u;
            instruction.offset = (instruction.offset & 0x80000000u) | strides[0];
            swizzle = 0x9250;
        } else {
            const uint32_t format = element->format;
            swizzle = (((format >> 16) & 7) | ((format >> 10) & 0x38));
            swizzle = (swizzle << 3) | ((format >> 19) & 7);
            swizzle = ((swizzle << 1) | (format & 0xFC00)) << 3;
            swizzle &= 0xFFFF;
            // Signed normalized formats swap selectors 0..3 with their signed variant.
            if ((format & 0xC0) == 0x40) {
                const uint32_t masks[] = {0xE000, 0x1C00, 0x380, 0x70};
                const uint32_t limits[] = {0x6000, 0xC00, 0x180, 0x30};
                const uint32_t toggles[] = {0x2000, 0x400, 0x80, 0x10};
                for (unsigned lane = 0; lane < 4; ++lane) {
                    if ((swizzle & masks[lane]) <= limits[lane]) swizzle ^= toggles[lane];
                }
            }
            instruction.format = (instruction.format & 0xBFC0CFFFu) |
                ((((rotateFetchWord(format, 12) & 0x3F000) | (format & 0x300)) << 4));
            const uint32_t streamBits = (0x5Fu - element->stream) * 0x01560056u;
            const uint32_t stream = (streamBits & ~0x00F80000u) |
                                   (rotateFetchWord(streamBits, 11) & 0x00F80000u);
            instruction.opcode = ((instruction.opcode & ~0x07F00000u) |
                                   (rotateFetchWord(stream, 1) & 0x07F00000u)) & 0xC7FFFFFFu;
            instruction.offset = (instruction.offset & 0x80000000u) |
                                 ((uint32_t(element->offset) << 6) & 0x7FFFFF00u) | strides[element->stream];
        }
        // The compiler's uninitialized low swizzle nibble is masked away by
        // every table entry. Bits 1..3 are then forced to one (constant lanes).
        swizzle |= 0xE;
        auto selected = [&](unsigned selector) {
            return uint32_t(g_grcFetchSwizzleMasks[selector] & swizzle);
        };
        uint32_t bits = selected(instruction.format & 7);
        uint32_t folded = bits;
        for (unsigned n = 0; n < 4; ++n) folded = (folded >> 3) | bits;
        instruction.format = (instruction.format & ~7u) | ((folded >> 1) & 7);
        bits = selected((instruction.format >> 3) & 7);
        folded = bits;
        for (unsigned n = 0; n < 3; ++n) folded = (folded >> 3) | bits;
        instruction.format = (instruction.format & ~0x38u) | (((folded >> 1) | (bits << 2)) & 0x38);
        bits = selected((instruction.format >> 6) & 7);
        folded = (bits >> 3) | bits;
        folded = (folded >> 3) | bits;
        instruction.format = (instruction.format & ~0x1C0u) |
                             (((folded >> 1) | (((bits << 3) | bits) << 2)) & 0x1C0);
        bits = selected((instruction.format >> 9) & 7);
        instruction.format = (instruction.format & ~0xE00u) |
            ((((((bits << 3) | bits) << 3) | bits) << 2 | (((bits >> 3) | bits) >> 1)) & 0xE00);
        patched[i] = instruction;
    }

    uint32_t next = 0;
    while (next < count) {
        while (next < count && !(input->fetchLocations[next] & 0x300000)) ++next;
        const uint32_t first = next++;
        if (next >= count) break;
        while (next < count && !(input->fetchLocations[next] & 0x300000)) ++next;
        if (next >= count) break;
        const uint32_t end = next++;
        const bool fixedLast = (input->fetchLocations[end] & 0x300000) == 0x300000;
        const uint32_t sortEnd = fixedLast ? end : end + 1;
        const int32_t lastConstant = fixedLast ? int32_t(fetchConstantIndex(patched[end].opcode)) : -1;
        // Selection sort, including the original tie breaks and swap order.
        for (uint32_t a = first; a + 1 < sortEnd; ++a) {
            for (uint32_t b = a + 1; b < sortEnd; ++b) {
                const auto& left = patched[a];
                const auto& right = patched[b];
                const int32_t leftConstant = int32_t(fetchConstantIndex(left.opcode));
                const int32_t rightConstant = int32_t(fetchConstantIndex(right.opcode));
                int32_t order = rightConstant - leftConstant;
                bool swap = leftConstant == lastConstant && order != 0;
                if (order != 0) {
                    if (rightConstant == lastConstant) order = -1;
                } else {
                    order = fetchOffset(left.offset) - fetchOffset(right.offset);
                    if (!order) order = int32_t(g_grcFetchFormatSizes[(left.format >> 16) & 63]) -
                                        int32_t(g_grcFetchFormatSizes[(right.format >> 16) & 63]);
                }
                if (swap || order > 0) {
                    const auto temp = patched[a];
                    patched[a] = patched[b];
                    patched[b] = temp;
                }
            }
        }
        uint32_t burst = first;
        for (uint32_t i = first + 1; i <= end; ++i) {
            auto& head = patched[burst];
            const auto& current = patched[i];
            const uint32_t headOffset = uint32_t(fetchOffset(head.offset));
            const uint32_t currentOffset = uint32_t(fetchOffset(current.offset));
            const uint32_t span = currentOffset - headOffset + g_grcFetchFormatSizes[(current.format >> 16) & 63];
            if (fetchConstantIndex(head.opcode) == fetchConstantIndex(current.opcode) &&
                headOffset <= currentOffset && span <= 8) {
                uint32_t length = (head.opcode >> 27) & 7;
                if (length <= span - 1) length = span - 1;
                head.opcode = (head.opcode & ~0x38000000u) | ((length << 27) & 0x38000000u);
                patched[i].format |= 0x40000000u;
            } else {
                burst = i;
            }
        }
    }
    auto* code = reinterpret_cast<grcFetchInstruction*>(static_cast<uintptr_t>(codeAddress));
    for (uint32_t i = 0; i < count; ++i) code[input->fetchLocations[i] & 0xFFF] = patched[i];
}

// Bind vertex/pixel programs, refresh cached vertex patches and derive depth state.
// @ 0x82363500
void grcDevice_ApplyShaderState(void* device) {
    // Xenon device/shader layouts contain 32-bit addresses. The command cursor
    // points at the last word written; each packet starts at cursor + 1.
    auto word = [](void* base, uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(base) + offset);
    };
    auto wide = [](void* base, uint32_t offset) -> uint64_t& {
        return *reinterpret_cast<uint64_t*>(static_cast<uint8_t*>(base) + offset);
    };
    auto byte = [](void* base, uint32_t offset) -> uint8_t& {
        return *(static_cast<uint8_t*>(base) + offset);
    };
    auto pointer = [&](void* base, uint32_t offset) -> void* {
        return reinterpret_cast<void*>(static_cast<uintptr_t>(word(base, offset)));
    };
    auto commands = [&]() -> uint32_t* {
        if (word(device, 0) > word(device, 8)) {
            return static_cast<uint32_t*>(rage_A980(device));
        }
        return static_cast<uint32_t*>(pointer(device, 0));
    };
    auto publish = [&](uint32_t* cursor) {
        word(device, 0) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(cursor));
    };

    void* vertexShader = pointer(device, 0x3294);
    void* pixelShader = pointer(device, 0x3290);
    void* declaration = pointer(device, 0x2C90);
    void* vertexInfo = static_cast<uint8_t*>(vertexShader) + word(vertexShader, 0x264) + 0x250;
    void* pixelInfo = pixelShader
        ? static_cast<uint8_t*>(pixelShader) + word(pixelShader, 0x48) + 0x34 : nullptr;
    uint32_t programControl = word(vertexInfo, 0);
    uint32_t contextMisc = word(vertexInfo, 4);
    uint32_t repatch = pixelInfo
        ? ((word(pixelInfo, 0x10) ^ word(vertexInfo, 0x10)) & 0x7FFFF) != 0
        : (word(vertexInfo, 0x10) & 0x1F) != 0;

    bool copyVertexCode = (byte(device, 0x28C1) & 1) != 0 || repatch != 0;
    if (!copyVertexCode && (wide(device, 0x30) & 0x80) != 0) {
        const uint32_t codeAddress = word(vertexShader, 0x28);
        if (declaration) {
            const bool patchChanged = word(vertexShader, 0xC) != word(declaration, 0x20)
                || (((wide(device, 0x3190) ^ wide(vertexShader, 0x18)) & wide(declaration, 0x10))
                    | ((wide(device, 0x3198) ^ wide(vertexShader, 0x20)) & wide(declaration, 0x18))) != 0;
            if (patchChanged) {
                const uint32_t fence = word(device, 0x289C);
                // Repatch in place only when the cached code is no longer in flight.
                copyVertexCode = (word(vertexShader, 0x24C) & 0x80000000) != 0
                    && (fence == 0 || fence - word(vertexShader, 8) < fence - word(pointer(device, 0x2890), 0));
                if (!copyVertexCode) {
                    grcPatchVertexFetchInstructions(device, vertexShader, codeAddress, declaration);
                    const uint32_t start = word(vertexShader, 0x28);
                    rage_EEC0(reinterpret_cast<void*>(static_cast<uintptr_t>(start)),
                              reinterpret_cast<void*>(static_cast<uintptr_t>(start + word(vertexShader, 0x258))));
                    if (word(declaration, 0x20) == 0) {
                        uint32_t serial;
                        // lwarx/stwcx, with 0 and UINT32_MAX reserved as invalid IDs.
                        do {
                            serial = __atomic_add_fetch(&g_grcShaderPatchSerial, 1u, __ATOMIC_RELAXED);
                        } while (serial + 1u < 2u);
                        word(declaration, 0x20) = serial;
                    }
                    word(vertexShader, 0xC) = word(declaration, 0x20);
                    word(vertexShader, 0x24C) |= 0x80000000;
                    wide(vertexShader, 0x18) = wide(device, 0x3190);
                    wide(vertexShader, 0x20) = wide(device, 0x3198);
                }
            }
        }
        if (!copyVertexCode) {
            uint32_t* cursor = commands();
            *++cursor = 0xC0003B00;  // INVALIDATE_STATE
            *++cursor = 0x7FFF;
            *++cursor = 0xC0012700;  // IM_LOAD: vertex shader
            *++cursor = (codeAddress & 0x1FFFFFFF) + (((codeAddress >> 20) + 0x200) & 0x1000);
            *++cursor = word(vertexShader, 0x258) >> 2;
            publish(cursor);
            word(vertexShader, 8) = word(device, 0x289C);
            wide(device, 0x2CA0) = wide(device, 0x3190);
            wide(device, 0x2CA8) = wide(device, 0x3198);
        }
    }
    if (copyVertexCode) {
        rage_32F0(device, repatch, vertexShader, &programControl, declaration, vertexInfo, pixelInfo);
    }

    if (!pixelInfo) {
        if ((word(device, 0x2D94) & 7) != 5) {
            grc_3410(device);
        }
    } else {
        programControl |= word(pixelInfo, 0);
        contextMisc |= word(pixelInfo, 4);
        if ((programControl & 0x70000000) > 0x10000000) {
            byte(device, 0x28C2) |= 0x20;
        }
        if ((wide(device, 0x30) & 0x100) != 0) {
            uint32_t* cursor = commands();
            *++cursor = 0xC0003B00;
            *++cursor = 0x7FFF;
            *++cursor = 0xC0012700;  // IM_LOAD: pixel shader (low bit = 1)
            const uint32_t address = word(pixelShader, 0xC);
            *++cursor = ((address & 0x1FFFFFFE) + (((address >> 20) + 0x200) & 0x1000)) | 1;
            *++cursor = word(pixelShader, 0x3C) >> 2;
            publish(cursor);
            word(pixelShader, 8) = word(device, 0x289C);
            word(device, 0x2D68) = word(pixelInfo, 0x18);
            wide(device, 0x28) |= uint64_t(7) << 40;

            if ((word(device, 0x2D94) & 7) == 5) {
                word(device, 0x2D94) = (word(device, 0x2D94) & ~7u) | 4;
                word(device, 0x2CF4) = 0;
                cursor = commands();
                *++cursor = 0x200D;
                *++cursor = word(device, 0x2CF4);
                *++cursor = 0x2208;
                *++cursor = word(device, 0x2D94);
                wide(device, 0x20) |= 0x10000;
                wide(device, 0x28) |= 0x20000000;
                publish(cursor);
            }
            uint32_t shaderControl = word(device, 0x28A0);
            if ((shaderControl & 0x100) != 0) {
                if ((programControl & 0x08000000) != 0) {
                    shaderControl &= ~0x100u;
                }
                cursor = commands();
                *++cursor = 0x5C8;
                *++cursor = 0x20000;
                *++cursor = 0xF01;
                *++cursor = shaderControl;
                publish(cursor);
            }
        }
    }

    word(device, 0x2D60) = programControl;
    word(device, 0x2D64) = contextMisc;
    wide(device, 0x28) |= uint64_t(3) << 41;
    if ((wide(device, 0x30) & 0x20) != 0) {
        const bool shaderExportsDepth = pixelInfo && (word(pixelInfo, 0) & 0x08000000) != 0;
        const uint32_t depthControl = word(device, 0x2D74);
        const uint32_t depthEnabled = depthControl >> 1;
        uint32_t renderControl = (word(device, 0x2D80) & ~1u)
            | ((byte(device, 0x28C2) >> 7) & depthEnabled);
        word(device, 0x2D80) = renderControl;
        const uint32_t depthFunc = (depthControl >> 4) & 7;
        const bool reversed = (renderControl & 0x10) != 0;
        bool earlyDepth = reversed ? (depthFunc == 4 || depthFunc == 6) : (depthFunc == 1 || depthFunc == 3);
        earlyDepth = earlyDepth && !shaderExportsDepth && (renderControl & depthEnabled & 1) != 0;
        if ((depthControl & 1) != 0) {
            earlyDepth = earlyDepth && (depthControl & 0x3800) == 0 && (depthControl & 0xE0000) == 0;
            if ((depthControl & 0x80) != 0) {
                earlyDepth = earlyDepth && (depthControl & 0x03800000) == 0 && (depthControl & 0xE0000000) == 0;
            }
        }
        renderControl = (renderControl & ~2u) | (uint32_t(earlyDepth) << 1);
        word(device, 0x2D80) = renderControl;
        if (earlyDepth) {
            if ((byte(device, 0x28C1) & 8) != 0) {
                byte(device, 0x28C1) &= 0xF7;
                uint32_t* cursor = commands();
                *++cursor = 0xC0004600;  // EVENT_WRITE
                *++cursor = 0xF;
                publish(cursor);
            }
        } else if ((depthEnabled & 1) != 0 && (depthControl & 4) != 0) {
            const bool lateDepth = depthFunc == 7 || depthFunc == 5
                || (reversed ? (depthFunc == 1 || depthFunc == 3) : (depthFunc == 4 || depthFunc == 6));
            if (lateDepth) {
                byte(device, 0x28C1) |= 8;
            }
        }
        wide(device, 0x28) |= uint64_t(1) << 34;
    }

    if ((byte(device, 0x28C0) & 0x20) != 0) {
        if ((wide(device, 0x28) & 0x20000000) != 0) {
            uint32_t* cursor = commands();
            *++cursor = 0x2208;
            *++cursor = word(device, 0x2D94);
            publish(cursor);
            wide(device, 0x28) &= ~uint64_t(0x20000000);
        }
        const uint32_t modeControl = word(device, 0x2D94);
        uint32_t mode = modeControl & 7;
        if ((word(device, 0x2D7C) & 8) == 0 && (word(pixelInfo, 0x1C) & 0x30) == 0) {
            mode = 5;
        }
        if (mode != word(device, 0x3298)) {
            word(device, 0x3298) = mode;
            uint32_t* cursor = commands();
            *++cursor = 0xC0015000;
            *++cursor = 0x15555555;
            *++cursor = 0;
            *++cursor = 0xC0012D01;
            *++cursor = 0x40208;
            *++cursor = (modeControl & ~7u) | mode;
            *++cursor = 0xC0015000;
            *++cursor = word(device, 0x32A0) != 0 ? word(device, 0x32A0) : 0xFFFFFFFF;
            *++cursor = 0;
            publish(cursor);
        }
    }
}

// Writes a contiguous register run, flushing the command buffer if needed.
extern uint32_t* grcDevice_WriteRegisterRunOverflow(void* device, uint32_t* cursor,
                                                    uint32_t firstRegister, const uint32_t* valuesBeforeRun,
                                                    uint32_t count, uint32_t stride); // @ 0x823625A0

// Callers supply a nonzero mask; bit 63 corresponds to values[0].
// @ 0x82362658
void grcDevice_FlushDirtyRegisterGroup(void* device, uint64_t dirty, uint32_t firstRegister,
                                       const uint32_t* values) {
    auto* state = static_cast<uint32_t*>(device);
    auto* cursor = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(state[0]));
    uint32_t offset = 0;
    do {
        const uint32_t skip = static_cast<uint32_t>(__builtin_clzll(dirty));
        dirty = skip == 64 ? 0 : dirty << skip;
        offset += skip;
        firstRegister += skip;
        const uint32_t count = dirty == UINT64_MAX ? 64 : static_cast<uint32_t>(__builtin_clzll(~dirty));
        if (static_cast<uint32_t>(reinterpret_cast<uintptr_t>(cursor) + count * 4) >= state[1]) {
            const auto before = reinterpret_cast<const uint32_t*>(
                reinterpret_cast<uintptr_t>(values) + offset * 4 - 4);
            cursor = grcDevice_WriteRegisterRunOverflow(device, cursor, firstRegister, before, count, 1);
            offset += count;
            dirty = count == 64 ? 0 : dirty << count;
        } else {
            *++cursor = ((count - 1) << 16) | firstRegister;
            for (uint32_t i = 0; i < count; ++i) {
                *++cursor = values[offset++];
                dirty <<= 1;
            }
        }
        firstRegister += count;
    } while (dirty != 0);
    state[0] = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(cursor));
}

// @ 0x82362980
void grcDevice_RefreshVertexFetchState(void* device) {
    auto* data = static_cast<uint8_t*>(device);
    auto word = [](void* base, uint32_t offset) -> uint32_t& {
        return *reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(base) + offset);
    };
    auto wide = [](void* base, uint32_t offset) -> uint64_t& {
        return *reinterpret_cast<uint64_t*>(static_cast<uint8_t*>(base) + offset);
    };
    auto* declaration = reinterpret_cast<void*>(static_cast<uintptr_t>(word(device, 0x2C90)));
    if (declaration == nullptr) {
        return;
    }

    uint32_t remaining = word(declaration, 12) + 1;
    uint32_t selector = 0x5AAB6;
    uint32_t i = 0;
    do {
        const uint32_t offset = word(device, 0x310C + i * 8);
        auto* buffer = reinterpret_cast<void*>(static_cast<uintptr_t>(word(device, 0x3110 + i * 8)));
        if (buffer != nullptr) {
            const uint32_t address = word(buffer, 12) + offset;
            const uint32_t size = word(buffer, 16) - offset;
            word(data, 0x77C - i * 8) = (size & ~0x30000000u) | 0x10000000u;
            word(data, 0x778 - i * 8) = (address & 0x1FFFFFFFu) + (((address >> 20) + 512) & 0x1000);
            const uint32_t shift = ((selector >> 16) + 26) & 127;
            wide(device, 0x20) |= shift < 64 ? (uint64_t(1) << 63) >> shift : 0;
        }
        ++i;
        selector -= 0x5556;
    } while (--remaining != 0);
    if (wide(device, 0x2CA0) != wide(device, 0x3190)
        || wide(device, 0x2CA8) != wide(device, 0x3198)) {
        wide(device, 0x30) |= 0x80;
    }
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
            grcDevice_RefreshVertexFetchState(device);
        }
        if ((dirty(0x30) & 0x1E0) != 0) {
            grcDevice_ApplyShaderState(device);
        }
        uint64_t mask = dirty(0x30) & 0xFFFFFFFFFC000000ULL;
        if (mask != 0) {
            grcDevice_FlushDirtyRegisterGroup(device, mask, 0x2300, reinterpret_cast<const uint32_t*>(data + 0x2DF8));
        }
        if ((dirty(0x30) & 0x03FC0000) != 0) {
            mask = (dirty(0x30) << 38) & 0xFF00000000000000ULL;
            grcDevice_FlushDirtyRegisterGroup(device, mask, 0x2380, reinterpret_cast<const uint32_t*>(data + 0x2E90));
        }
        dirty(0x30) = 0;
    }

    // Vertex and pixel float constants, 16 dwords per dirty bit.
    if (dirty(0x10) != 0) {
        grcDevice_FlushDirtySixteenRegisterGroups(device, dirty(0x10), 0x4000,
                                                  reinterpret_cast<const uint32_t*>(data + 0x780));
        dirty(0x10) = 0;
    }
    if (dirty(0x18) != 0) {
        grcDevice_FlushDirtySixteenRegisterGroups(device, dirty(0x18), 0x4400,
                                                  reinterpret_cast<const uint32_t*>(data + 0x1780));
        dirty(0x18) = 0;
    }

    if (dirty(0x20) != 0) {
        uint64_t mask = dirty(0x20) & 0xFFFFFFFF00000000ULL;
        if (mask != 0) {
            // Six dwords per vertex fetch descriptor.
            grcDevice_FlushDirtySixRegisterGroups(device, mask, 0x4800, reinterpret_cast<const uint32_t*>(data + 0x480));
        }
        if ((dirty(0x20) & 0x80000000) != 0) {
            // lis -256 sign-extends on Xenon, including the upper 32 bits.
            dirty(0x2CB0) = 0xFFFFFFFFFF000000ULL;
            grcDevice_FlushDirtyRegisterGroup(device, 0xFFFFFFFFFF000000ULL, 0x4900, reinterpret_cast<const uint32_t*>(data + 0x2780));
        }
        if ((dirty(0x20) & 0x3FFFC000) != 0) {
            mask = (dirty(0x20) << 34) & 0xFFFF000000000000ULL;
            grcDevice_FlushDirtyRegisterGroup(device, mask, 0x2000, reinterpret_cast<const uint32_t*>(data + 0x2CC0));
        }
        dirty(0x20) = 0;
    }

    if (dirty(0x28) != 0) {
        uint64_t mask = dirty(0x28) & 0xFFFFF80000000000ULL;
        if (mask != 0) {
            grcDevice_FlushDirtyRegisterGroup(device, mask, 0x2100, reinterpret_cast<const uint32_t*>(data + 0x2D0C));
        }
        if ((dirty(0x28) & 0x000007C000000000ULL) != 0) {
            mask = (dirty(0x28) << 21) & 0xF800000000000000ULL;
            grcDevice_FlushDirtyRegisterGroup(device, mask, 0x2180, reinterpret_cast<const uint32_t*>(data + 0x2D60));
        }
        if ((dirty(0x28) & 0x0000003FFC000000ULL) != 0) {
            mask = (dirty(0x28) << 26) & 0xFFF0000000000000ULL;
            grcDevice_FlushDirtyRegisterGroup(device, mask, 0x2200, reinterpret_cast<const uint32_t*>(data + 0x2D74));
        }
        if ((dirty(0x28) & 0x03FFFFE0) != 0) {
            mask = (dirty(0x28) << 38) & 0xFFFFF80000000000ULL;
            grcDevice_FlushDirtyRegisterGroup(device, mask, 0x2280, reinterpret_cast<const uint32_t*>(data + 0x2DA4));
        }
        dirty(0x28) = 0;
    }
}

// Each dirty bit selects six consecutive registers; callers pass a nonzero mask.
// @ 0x82362718
void grcDevice_FlushDirtySixRegisterGroups(void* device, uint64_t dirty, uint32_t /* firstRegister */,
                                           const uint32_t* values) {
    auto* state = static_cast<uint32_t*>(device);
    auto* cursor = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(state[0]));
    uint32_t firstRegister = 0x4800;
    uint32_t offset = 0;
    do {
        const uint32_t skip = static_cast<uint32_t>(__builtin_clzll(dirty));
        dirty <<= skip;
        offset += skip * 6;
        firstRegister += skip * 6;
        const uint32_t count = dirty == UINT64_MAX ? 64 : static_cast<uint32_t>(__builtin_clzll(~dirty));
        const uint32_t words = count * 6;
        if (static_cast<uint32_t>(reinterpret_cast<uintptr_t>(cursor) + words * 4 + 4) >= state[1]) {
            const auto before = reinterpret_cast<const uint32_t*>(
                reinterpret_cast<uintptr_t>(values) + offset * 4 - 4);
            cursor = grcDevice_WriteRegisterRunOverflow(device, cursor, firstRegister, before, words, 6);
            offset += words;
            dirty = count == 64 ? 0 : dirty << count;
        } else {
            cursor[1] = 0x80000000;
            cursor = reinterpret_cast<uint32_t*>(reinterpret_cast<uintptr_t>(cursor)
                                                  + (reinterpret_cast<uintptr_t>(cursor) & 7));
            *++cursor = ((words - 1) << 16) | firstRegister;
            for (uint32_t i = 0; i < words; ++i) {
                *++cursor = values[offset++];
            }
            dirty = count == 64 ? 0 : dirty << count;
        }
        firstRegister += words;
    } while (dirty != 0);
    state[0] = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(cursor));
    if (state[0] > state[2]) {
        cursor = static_cast<uint32_t*>(rage_A980(device));
    }
    *++cursor = 0x25000;
    *++cursor = 0;
    *++cursor = 0;
    *++cursor = 0;
    state[0] = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(cursor));
}

// Each dirty bit selects sixteen consecutive registers; callers pass a nonzero mask.
// @ 0x82362858
void grcDevice_FlushDirtySixteenRegisterGroups(void* device, uint64_t dirty, uint32_t firstRegister,
                                               const uint32_t* values) {
    auto* state = static_cast<uint32_t*>(device);
    auto* cursor = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(state[0]));
    uint32_t offset = 0;
    do {
        const uint32_t skip = static_cast<uint32_t>(__builtin_clzll(dirty));
        dirty <<= skip;
        offset += skip * 16;
        firstRegister += skip * 16;
        const uint32_t count = dirty == UINT64_MAX ? 64 : static_cast<uint32_t>(__builtin_clzll(~dirty));
        const uint32_t words = count * 16;
        if (static_cast<uint32_t>(reinterpret_cast<uintptr_t>(cursor) + (words + 3) * 4) >= state[1]) {
            const auto before = reinterpret_cast<const uint32_t*>(
                reinterpret_cast<uintptr_t>(values) + offset * 4 - 4);
            cursor = grcDevice_WriteRegisterRunOverflow(device, cursor, firstRegister, before, words, 16);
        } else {
            cursor[1] = cursor[2] = cursor[3] = 0x80000000;
            cursor = reinterpret_cast<uint32_t*>(reinterpret_cast<uintptr_t>(cursor)
                                                  + ((-8u - reinterpret_cast<uintptr_t>(cursor)) & 15));
            *++cursor = ((words - 1) << 16) | firstRegister;
            for (uint32_t i = 0; i < words; ++i) {
                *++cursor = values[offset + i];
            }
        }
        offset += words;
        firstRegister += words;
        dirty = count == 64 ? 0 : dirty << count;
    } while (dirty != 0);
    state[0] = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(cursor));
}


extern uint32_t KeGetCurrentProcessType(); // @ 0x82585E9C
extern uint32_t xe_GetCurrentThreadId(); // @ 0x82566B78
extern void rage_AA78(void* device, uint32_t* fence); // @ 0x8235AA78
extern const uint32_t __imp_VdGlobalDevice; // @ 0x82000730
extern const uint32_t __imp_VdGlobalXamDevice; // @ 0x82000734

static void* resourceKernelDevice() {
    const uint32_t slot = KeGetCurrentProcessType() == 2 ? __imp_VdGlobalXamDevice : __imp_VdGlobalDevice;
    return reinterpret_cast<void*>(uintptr_t(*reinterpret_cast<const uint32_t*>(uintptr_t(slot))));
}

static uint32_t resourceGpuAddress(uint32_t address) {
    return (address & 0x1FFFFFFFu) + (((address >> 20) + 0x200u) & 0x1000u);
}

static uint32_t& resourceDeviceWord(void* device, uint32_t offset) {
    return *reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(device) + offset);
}

// Wait for the resource fence, invalidate its CPU-visible range, record dirty
// cache lines and increment its lock count. Flags can request an aperture alias.
// grcResource_Lock @ 0x823529E0 | size: 0x2E8
uint32_t grcResource_Lock(void* resource, uint32_t fence, uint32_t /*unusedR5*/,
                          uint32_t auxiliary, uint32_t base, uint32_t auxiliaryBase,
                          uint32_t data, uint32_t size, uint32_t flags, uint32_t cacheFlags) {
    auto* control = static_cast<uint32_t*>(resource);
    if ((flags & 0x1010u) == 0 && fence != 0) {
        void* device = resourceKernelDevice();
        uint32_t pending = fence;
        const uint32_t thread = xe_GetCurrentThreadId();
        const bool ownedThread = thread == resourceDeviceWord(device, 0x2888);
        const bool shared = control && (control[0] & 0x00F80000u) != 0;
        if (shared) fence = resourceDeviceWord(device, 0x289C);
        if (fence != 0 && shared && ownedThread)
            pending = resourceDeviceWord(device, 0x289C);
        if (pending != 0) rage_AA78(device, &pending);
    }
    if ((flags & 0x12u) == 0) {
        void* device = resourceKernelDevice();
        const uint32_t start = resourceGpuAddress(data);
        const uint32_t end = start + size;
        if (xe_GetCurrentThreadId() != resourceDeviceWord(device, 0x2888)) {
            auto* range = reinterpret_cast<uint64_t*>(static_cast<uint8_t*>(device) + 0x2C98);
            uint64_t observed = __atomic_load_n(range, __ATOMIC_RELAXED);
            uint64_t desired;
            do {
                const uint32_t oldStart = uint32_t(observed);
                const uint32_t oldEnd = uint32_t(observed >> 32);
                const uint32_t mergedStart = start < oldStart ? start : oldStart;
                const uint32_t mergedEnd = end > oldEnd ? end : oldEnd;
                desired = (uint64_t(mergedEnd) << 32) | mergedStart;
            } while (!__atomic_compare_exchange_n(range, &observed, desired, false,
                                                  __ATOMIC_RELAXED, __ATOMIC_RELAXED));
        } else {
            auto* cursor = reinterpret_cast<uint32_t*>(uintptr_t(resourceDeviceWord(device, 0)));
            if (resourceDeviceWord(device, 0) > resourceDeviceWord(device, 8))
                cursor = static_cast<uint32_t*>(rage_A980(device));
            const uint32_t pageStart = start & ~0xFFFu;
            const uint32_t pageBytes = ((end + 0xFFFu) & ~0xFFFu) - pageStart;
            *++cursor = 0xA31;
            *++cursor = cacheFlags;
            *++cursor = 0x10A2F;
            *++cursor = pageBytes;
            *++cursor = pageStart;
            *++cursor = 0xC0043C00u;
            *++cursor = 3;
            *++cursor = 0xA31;
            *++cursor = 0;
            *++cursor = 0x80000000u;
            *++cursor = 8;
            resourceDeviceWord(device, 0) = uint32_t(reinterpret_cast<uintptr_t>(cursor));
        }
    }
    const bool aperture = (flags & 0x10u) != 0;
    if (aperture || (control[0] & 0x40000000u) != 0) {
        if ((flags & 1) == 0) {
            const bool second = auxiliary != 0 && auxiliaryBase != 0;
            uint32_t& dirty = control[second ? 3 : 2];
            const uint32_t offset = data - (second ? auxiliaryBase : base);
            const uint32_t lineStart = offset >> 7;
            const uint32_t lineEnd = (offset + size + 127u) >> 7;
            const uint32_t oldStart = dirty >> 16, oldEnd = dirty & 0xFFFFu;
            dirty = ((lineStart < oldStart ? lineStart : oldStart) << 16)
                  | (lineEnd > oldEnd ? lineEnd : oldEnd);
        }
        if (aperture) data = resourceGpuAddress(data) - 0x40000000u;
    }
    control[0] += 0x1000;
    return data;
}

} // extern "C"
