/**
 * rage_grm.cpp — Graphics / rendering class implementations
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 */
#include "rage_grm.hpp"
#include "animation/rage_anim.hpp"   // rage::datResource

// Forward declarations for external functions
extern "C" void fragDrawable_0AA0_2h(void* state, void* geom, void* drawable, int index, void* param); // @ 0x820F0AA0
extern "C" void* g_iccProfilePtr;     // @ 0x825EB1D0
extern "C" void* g_currentGeometry;   // @ 0x82606350

// Helpers used by lifted dispatch methods (all raw recomp stubs).
extern "C" void   rage_free_00C0(uint32_t ptr);              // @ 0x820C00C0
extern "C" void   rage_free(void* ptr);                      // @ 0x820C00C0
extern "C" void   rage_0F38(void* self);                     // @ 0x820F0F38
extern "C" void   net_2228_h(void* self);                    // @ 0x820F2228
extern "C" void   rage_1028(uint32_t a, uint32_t b,          // @ 0x820F1028
                            uint32_t c, uint32_t d,
                            uint32_t e);
extern "C" void   grmModelFactory_sm_DeclMap_dtor(void* self); // @ 0x820F3CA0
// grmModel rsc constructor (installs the grmModel vtable 0x8202F3B4).
extern "C" void   ke_1ED8(rage::grmModel* model,             // @ 0x820F1ED8
                          rage::datResource& rsc);
extern "C" void   ke_2160(uint32_t chunk);                   // @ 0x820F2160
// grmShaderGroup rsc constructor (installs the grmShaderGroup vtable 0x8202F528).
extern "C" void   fragDrawable_3010(rage::grmShaderGroup* group, // @ 0x820F3010
                                    rage::datResource& rsc);
extern "C" void   grcSetup_vfn_2_CFD0_1(void* self);         // @ 0x8215CFD0
extern "C" void   xe_main_thread_init_0038();                // @ 0x820C0038

// SDA-resident globals (r13+0 chain / factory-singleton pointer).
extern "C" uint32_t g_rageDescriptorHead;                    // @ 0x82600000
extern "C" rage::grmShaderFactory* g_grmShaderFactory_instance; // @ 0x82606374

namespace rage {

// ── rage::spdApical ───────────────────────────────────────────────────────────

void spdApical::SetLodNear(float value) {
    unk_10 = value;
}

void spdApical::SetLodFar(float value) {
    unk_14 = value;
}

void spdApical::SetLodFadeStart(float value) {
    unk_18 = value;
}

void spdApical::SetLodFadeEnd(float value) {
    unk_1C = value;
}

// ── rage::fragDrawable ────────────────────────────────────────────────────────

/**
 * fragDrawable::ProcessGeometry
 * @ 0x820F1C00 | size: 0x17c
 *
 * Original symbol: fragDrawable_1C00_fw. Only caller: 0x8225D9E4 (rmcDrawable).
 * `this` looks like a grmModel (u16 shader indices at +0x0C, count at +0x16);
 * geometryContainer holds the shader array pointer at +8.
 *
 * For each index i whose shader passes the filter, either hands it to
 * 0x820F0AA0 (when the override at 0x825EB1D0 is set) or calls the shader's
 * slot 4 with an "end of run" flag that is set when the next index uses a
 * shader with a different id at +6. A forced shader (0x82606350) replaces the
 * lookup; if its flag bit 0 is set its type counts as 0.
 */
void fragDrawable::ProcessGeometry(void* geometryContainer, void* param1, void* param2,
                                   uint32_t filterType, void* param3) {
    if (m_geometryCount == 0) {
        return;
    }

    void* statePtr    = g_iccProfilePtr;
    void* currentGeom = g_currentGeometry;

    for (int i = 0; i < m_geometryCount; i++) {
        void* geom;
        uint32_t geomType;
        if (currentGeom != nullptr) {
            geom = currentGeom;
            uint16_t flags = *(uint16_t*)((uint8_t*)geom + 4);
            geomType = (flags & 1) ? 0 : (flags >> 5) & 0x1F;
        } else {
            void** shaders = *(void***)((uint8_t*)geometryContainer + 8);
            geom = shaders[m_pIndices[i]];
            geomType = (*(uint16_t*)((uint8_t*)geom + 4) >> 5) & 0x1F;
        }
        if ((int32_t)geomType != (int32_t)filterType) {
            continue;
        }

        if (statePtr != nullptr) {
            fragDrawable_0AA0_2h(statePtr, geom, this, i, param3);
            continue;
        }

        bool sameAsNext = true;
        if (currentGeom == nullptr) {
            if (i + 1 < m_geometryCount) {
                void** shaders = *(void***)((uint8_t*)geometryContainer + 8);
                void* nextGeom = shaders[m_pIndices[i + 1]];
                sameAsNext = *(uint16_t*)((uint8_t*)geom + 6) ==
                             *(uint16_t*)((uint8_t*)nextGeom + 6);
            } else {
                sameAsNext = false;
            }
        }
        bool endOfRun = (i + 1 == m_geometryCount) || !sameAsNext;

        typedef void (*GeomProcessFn)(void* geom, void* drawable, int index,
                                      void* param1, void* param2, void* param3,
                                      bool endOfRun);
        GeomProcessFn processFn = (GeomProcessFn)(*(void***)geom)[4];
        processFn(geom, this, i, param1, param2, param3, endOfRun);

        currentGeom = g_currentGeometry;
        statePtr    = g_iccProfilePtr;
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmModel::ScalarDtor                    [vtable slot 0]
 * @ 0x820F0E78 | size: 0x6C (108 bytes)
 *
 * Scalar-deleting destructor.  Installs grmModel's own vtable (0x8202F3B4),
 * frees the geometry buffer at +0x0C, drops to the rage::datBase base
 * vtable (0x820276C4), then frees the object itself when bit 0 of flags
 * is set.  r3 comes back as `this`.
 * ═══════════════════════════════════════════════════════════════════════════ */
grmModel* grmModel::ScalarDtor(int flags) {
    vtable = reinterpret_cast<void**>(0x8202F3B4u);
    rage_free(m_pGeometry);
    vtable = reinterpret_cast<void**>(0x820276C4u);  // rage::datBase
    if (flags & 1) {
        rage_free(this);
    }
    return this;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmModelGeom::ScalarDtor                [vtable slot 0]
 * @ 0x820F0EE8 | size: 0x50 (80 bytes)
 *
 * Scalar-deleting destructor: runs the non-deleting destructor body
 * rage_0F38 @ 0x820F0F38, then frees the object when bit 0 of flags is set.
 * ═══════════════════════════════════════════════════════════════════════════ */
grmModelGeom* grmModelGeom::ScalarDtor(int flags) {
    rage_0F38(this);
    if (flags & 1) {
        rage_free(this);
    }
    return this;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderGroup::ScalarDtor              [vtable slot 0]
 * @ 0x820F21D8 | size: 0x50 (80 bytes)
 *
 * Scalar-deleting destructor: runs the non-deleting destructor body
 * net_2228_h @ 0x820F2228, then frees the object when bit 0 of flags is
 * set.  r3 comes back as `this`.
 * ═══════════════════════════════════════════════════════════════════════════ */
grmShaderGroup* grmShaderGroup::ScalarDtor(int flags) {
    net_2228_h(this);
    if (flags & 1) {
        rage_free(this);
    }
    return this;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmModelFactory::ScalarDtor             [vtable slot 0]
 * @ 0x820F3C50 | size: 0x50 (80 bytes)
 *
 * Scalar-deleting destructor: runs the non-deleting destructor body at
 * 0x820F3CA0, then frees the object when bit 0 of flags is set.  r3 comes
 * back as `this`.
 * ═══════════════════════════════════════════════════════════════════════════ */
grmModelFactory* grmModelFactory::ScalarDtor(int flags) {
    grmModelFactory_sm_DeclMap_dtor(this);
    if (flags & 1) {
        rage_free(this);
    }
    return this;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmModelFactory::Dispatch5              [vtable slot 1]
 * @ 0x820F3D10 | size: 0x18 (24 bytes)
 *
 * Drops `this` and tail-calls rage_1028 @ 0x820F1028 with r4..r8 moved
 * down into r3..r7:
 *
 *     mr r3,r4; mr r4,r5; mr r5,r6; mr r6,r7; mr r7,r8
 *     b  0x820F1028
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmModelFactory::Dispatch5(uint32_t a, uint32_t b, uint32_t c,
                                uint32_t d, uint32_t e) {
    rage_1028(a, b, c, d, e);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmModelFactory::vfn_2                  [vtable slot 2]
 * @ 0x820F4CF0 | size: 0x48 (72 bytes)
 *
 * Relocates the caller's pointer field (r5) through the datResource in r4;
 * `this` (r3) is never read:
 *
 *     chunk  = *field
 *     if (chunk == 0) return
 *     base   = *(uint32_t*)(rsc + 0x04)
 *     stride = *(uint32_t*)(rsc + 0x4C)          (twllei trap if zero)
 *     idx    = (chunk - base) / stride + 2       ( +2 skips 8-byte hdr )
 *     step   = *(uint32_t*)(rsc + idx*4)
 *     next   = chunk + step
 *     *field = next
 *     if (next != 0) ke_1ED8(next, rsc)          (grmModel rsc constructor)
 *
 * That arithmetic is datResource::PointerFixup: rsc + 8 holds the
 * per-chunk deltas.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmModelFactory::vfn_2(datResource& rsc, grmModel*& model) {
    rsc.PointerFixup(model);
    if (model != nullptr) {
        ke_1ED8(model, rsc);
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFactory::ScalarDtor            [vtable slot 0]
 * @ 0x820F6E60 | size: 0x64 (100 bytes)
 *
 * Resets the vtable to grmShaderFactory's (0x8202F808), clears the global
 * instance pointer (0x82606374) if it is this, frees this if bit 0 of
 * flags is set, returns this.  Also slot 0 of grmShaderFactoryStandard.
 * ═══════════════════════════════════════════════════════════════════════════ */
grmShaderFactory* grmShaderFactory::ScalarDtor(int flags) {
    vtable = reinterpret_cast<void**>(0x8202F808u);
    if (g_grmShaderFactory_instance == this) {
        g_grmShaderFactory_instance = nullptr;
    }
    if (flags & 1) {
        rage_free(this);
    }
    return this;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFactoryStandard::Allocate40    [vtable slot 2]
 * @ 0x820F7490 | size: 0x64 (100 bytes)
 *
 * Allocates a 40-byte shader slot via the first registered descriptor's
 * own vtable-slot-1 allocator.  The descriptor lives at r13+0 (SDA head)
 * and the factory pulls the r11[4] entry (word index 1 == byte offset 4).
 *
 *     alloc = ((uint32_t*)g_rageDescriptorHead)[1]
 *     raw   = ((AllocFn)alloc->vtable[1])(alloc, 40, 16)
 *     if (!raw) return 0
 *     ke_2160(raw)
 *     return raw
 *
 * Size 40 / align 16 are the canonical grmShader dimensions for this
 * factory; callers rely on them being baked in.
 * ═══════════════════════════════════════════════════════════════════════════ */
uint32_t grmShaderFactoryStandard::Allocate40() {
    xe_main_thread_init_0038();
    auto* desc = reinterpret_cast<uint32_t*>(g_rageDescriptorHead);
    uint32_t allocator = desc[1];  // word-index 1 == byte offset 4
    using AllocFn = uint32_t (*)(uint32_t self, uint32_t size, uint32_t align);
    void** allocVT = *reinterpret_cast<void***>(allocator);
    AllocFn fn = reinterpret_cast<AllocFn>(allocVT[1]);
    uint32_t blk = fn(allocator, 40, 16);
    if (blk == 0) {
        return 0;
    }
    ke_2160(blk);
    return blk;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFactoryStandard::vfn_6         [vtable slot 6]
 * @ 0x820F7290 | size: 0x48 (72 bytes)
 *
 * Same body as grmModelFactory::vfn_2 — relocate the r5 pointer field
 * through the datResource in r4 — but the tail call is fragDrawable_3010
 * (the grmShaderGroup rsc constructor) rather than ke_1ED8.  Slot 7
 * (0x820F72D8) is a different, unlifted function.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmShaderFactoryStandard::vfn_6(datResource& rsc, grmShaderGroup*& group) {
    rsc.PointerFixup(group);
    if (group != nullptr) {
        fragDrawable_3010(group, rsc);
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmSetup::vfn_2                         [vtable slot 2]
 * @ 0x82378448 | size: 0x04 (4 bytes)
 *
 * Minimal pass-through: unconditional `b 0x8215CFD0` (i.e. tail-call the
 * base-class grcSetup slot-2 implementation).  Exists only because the
 * derived vtable layout demands a unique function pointer per slot.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmSetup::vfn_2() {
    grcSetup_vfn_2_CFD0_1(this);
}

} // namespace rage

namespace rage {

/* ═══════════════════════════════════════════════════════════════════════════
 * fragDrawable_41B8 @ 0x821241B8 | size: 0x68 (104 bytes)
 *
 * Compares two strings lexicographically.
 *
 * This function performs a signed byte-by-byte comparison of two null-terminated
 * strings, similar to strcmp but returns a boolean result.
 *
 * Parameters:
 *   pString1 - Pointer to first string (stored at offset +0 of first parameter)
 *   pString2 - Pointer to second string (stored at offset +0 of second parameter)
 *
 * Returns:
 *   1 (true) if string1 < string2 lexicographically
 *   0 (false) otherwise
 *
 * Algorithm:
 *   1. Load string pointers from offset +0 of each parameter
 *   2. Compare bytes while both are non-zero and equal
 *   3. When mismatch or null found, compare final bytes as signed chars
 *   4. Return 1 if first string's byte < second string's byte, else 0
 * ═══════════════════════════════════════════════════════════════════════════ */
uint8_t fragDrawable_41B8(void* pParam1, void* pParam2)
{
    /* Load string pointers from parameters */
    const char* str1 = *(const char**)pParam1;
    const char* str2 = *(const char**)pParam2;
    
    /* Compare strings byte-by-byte */
    while (*str1 != '\0' && *str1 == *str2) {
        str1++;
        str2++;
    }
    
    /* Compare final bytes as signed chars */
    int8_t byte1 = (int8_t)*str1;
    int8_t byte2 = (int8_t)*str2;
    
    /* Return 1 if str1 < str2, else 0 */
    return (byte1 < byte2) ? 1 : 0;
}

} // namespace rage

// ─────────────────────────────────────────────────────────────────────────────
//  rage::grmShaderFx — 10 vtable methods
//  Lifted from vtable @ 0x8202F2DC (see rage_grm.hpp).  Addresses cover the
//  contiguous 0x820EF060..0x820F0730 block of the effect-framework runtime.
// ─────────────────────────────────────────────────────────────────────────────
//
//  Global-state aliases (SDA / .data):
//    lbl_825EBA68 — g_grmShaderFx_activeState     (active-state flag cell)
//    lbl_825EBC4C — g_grmShaderFx_activeInstance  (current-shader pointer)
//    lbl_825EBC50 — g_grmShaderFx_boundParam      (last-uploaded param descriptor)
//    lbl_825EBC54 — g_grmShaderFx_boundContext    (context cached inside +16)
//    lbl_825EAF88 — g_grmShaderFx_registry        (shader-type registry, 512B)
//    lbl_825EBBD8 — g_grmShaderFx_variantTable    (forced-variant override root)
//    lbl_825C9A5C — g_grmShaderFx_forcedVariantId (-1 = use override table)
//    lbl_825C9A64 — g_grmShaderFx_defaultVariant  (fallback variant index)
//    lbl_825EBB1C — g_grmShaderFx_flushRequired   (post-bind flush latch)
//    lbl_825EBAB4 — g_grmShaderFx_forceResetFlag  (force-state-reset latch)
//    lbl_825C9010 — g_grmShaderFx_frameCounter    (frame-counter snapshot)
//
// File-scope extern "C" declarations (block-scope linkage-specs are illegal
// under [dcl.link]; all helper symbols live here).
extern "C" {
    // Collaborator functions already lifted / stubbed elsewhere.
    void     util_9CF0(uint32_t self);                     // @ 0x82159CF0
    void     rage_8C48(uint32_t descriptor, uint32_t data); // @ 0x82158C48
    void     rage_9E70(uint32_t paramDesc);                 // @ 0x82159E70
    void     rage_5BF8(uint32_t effectObj);                 // @ 0x82445BF8
    void     rage_A1F8(uint32_t target, uint32_t registry); // @ 0x8215A1F8
    void     rage_F340(uint32_t self);                      // @ 0x820EF340
    void     hudFlashBase_B138_g();                         // @ 0x8215B138
    void     grmShaderFx_AF90_w(uint32_t effectSlot,
                                uint32_t paramA,
                                uint32_t paramB);           // @ 0x8215AF90

    // SDA-resident globals used by the grmShaderFx runtime.
    extern uint32_t g_grmShaderFx_activeState;      // @ 0x825EBA68
    extern uint32_t g_grmShaderFx_activeInstance;   // @ 0x825EBC4C
    extern uint32_t g_grmShaderFx_boundParam;       // @ 0x825EBC50
    extern uint32_t g_grmShaderFx_boundContext;     // @ 0x825EBC54
    extern uint32_t g_grmShaderFx_registry[128];    // @ 0x825EAF88  (512-byte table)
    extern uint32_t g_grmShaderFx_variantTable[];   // @ 0x825EBBD8
    extern int32_t  g_grmShaderFx_forcedVariantId;  // @ 0x825C9A5C
    extern uint32_t g_grmShaderFx_defaultVariant;   // @ 0x825C9A64
    extern uint32_t g_grmShaderFx_flushRequired;    // @ 0x825EBB1C
    extern uint32_t g_grmShaderFx_forceResetFlag;   // @ 0x825EBAB4
    extern uint32_t g_grmShaderFx_frameCounter;     // @ 0x825C9010
}

namespace rage {

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShader::Reset                                    [vtable slot 7]
 * @ 0x820F5350 | size: 0x10 (16 bytes)
 *
 * Zeroes the active-shader cell 0x825EBA68 (g_grmShaderFx_activeState),
 * which grmShader's slot 6 (0x820F5330) points at `this`.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmShader::Reset() {
    g_grmShaderFx_activeState = 0;
}

// Small helper to recover the active variant index with the same
// decision tree the PPC bodies inline in every caller of the variant
// table.  Factored so vfn_6 and vfn_11 read identically.
static uint32_t grmShaderFx_resolveVariantIndex() {
    const int32_t forced = g_grmShaderFx_forcedVariantId;
    if (forced != -1) {
        return static_cast<uint32_t>(forced);
    }
    // No forced variant — consult the variant table root.  Word 1 of
    // lbl_825EBBD8 holds the "override present" flag; when non-zero
    // the override cell sits 4 bytes before g_grmShaderFx_defaultVariant.
    const uint32_t overrideFlag =
        reinterpret_cast<const uint32_t*>(&g_grmShaderFx_variantTable[0])[1];
    if (overrideFlag != 0) {
        return *(&g_grmShaderFx_defaultVariant - 1);
    }
    return g_grmShaderFx_defaultVariant;
}

// Each effect descriptor in g_grmShaderFx_registry has the RAGE shape:
//   +0x00  class-id / type tag           (uint32)
//   +0x20  variable-descriptor array     (ptr to 56-byte entries)
//   +0x24  variable count                (uint16 at +36)
// The lookup idiom in vfn_10/12/13/17 rotates m_shaderId left by 2 (≡ *4)
// to index the pointer table at lbl_825EAF88.
static inline uint32_t grmShaderFx_registryEntry(uint16_t shaderId) {
    return g_grmShaderFx_registry[shaderId];
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::Dispatch                               [vtable slot 6]
 * @ 0x820EFA08 | size: 0xDC (220 bytes)
 *
 * Top-level draw entry.  Publishes `this` as the active shader, captures
 * the current frame-counter into the per-shader snapshot slot at +44,
 * resolves the active variant index, conditionally flushes the render
 * state (when the flush-latch or force-reset flag is set), and then
 * delegates to grmShaderFx_AF90_w.
 *
 * Two call shapes:
 *   directEntry != 0  → use the caller-supplied entry pointer
 *   directEntry == 0  → index the per-variant pass table at
 *                       this->techniqueData[passIndex + variantBase]
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmShaderFx::Dispatch(uint32_t passIndex,
                           uint32_t callerContext,
                           uint32_t directEntry) {
    auto* self = reinterpret_cast<uint8_t*>(this);

    // Snapshot the frame counter into our per-instance slot (+44)
    // and publish `this` as the active shader.
    const uint32_t frame = g_grmShaderFx_frameCounter;
    g_grmShaderFx_activeState = reinterpret_cast<uintptr_t>(this);
    *reinterpret_cast<uint32_t*>(self + 44) = frame;

    // Resolve variant index (forced / override / default).
    const uint32_t variantIndex = grmShaderFx_resolveVariantIndex();

    // Post-publish render-state flush: either the flush latch is set
    // or a global force-reset is pending.  hudFlashBase_B138_g runs
    // the renderer's "drop all state" routine.
    if (g_grmShaderFx_flushRequired != 0 ||
        g_grmShaderFx_forceResetFlag != 0) {
        hudFlashBase_B138_g();
    }

    // Fast path: caller passed a direct entry — hand it straight to
    // the inner draw routine along with the effect object at +16.
    const uint32_t effectSlot = reinterpret_cast<uintptr_t>(self + 16);
    if (directEntry != 0) {
        grmShaderFx_AF90_w(effectSlot, directEntry, callerContext);
        return;
    }

    // Slow path: resolve the pass entry through the per-technique
    // array stored at this+64.  Index math mirrors the PPC rlwinm
    // idiom:  offset = ((variantIndex * 4) + passIndex) * 4.
    const uint32_t* techniqueData =
        *reinterpret_cast<uint32_t**>(self + 64);
    const uint32_t flatIndex = (variantIndex << 2) + passIndex;
    const uint32_t passEntry = techniqueData[flatIndex];
    grmShaderFx_AF90_w(effectSlot, passEntry, callerContext);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::ClearActive                            [vtable slot 7]
 * @ 0x820EFAE8 | size: 0x44 (68 bytes)
 *
 * Drops the active-shader binding.  Zeroes g_grmShaderFx_activeState,
 * hands the old g_grmShaderFx_activeInstance to util_9CF0 (the renderer's
 * shader-unbind routine), then clears the instance pointer.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmShaderFx::ClearActive() {
    g_grmShaderFx_activeState = 0;
    const uint32_t oldInstance = g_grmShaderFx_activeInstance;
    util_9CF0(oldInstance);
    g_grmShaderFx_activeInstance = 0;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::BindConstantSlot                       [vtable slot 8]
 * @ 0x820EF928 | size: 0x9C (156 bytes)
 *
 * Uploads constant-register slot `varIndex` into the active device
 * context and caches the resulting descriptor so that a subsequent
 * upload for the same slot can short-circuit.
 *
 * Steps (PPC order):
 *   1. Read the active shader instance via (&g_grmShaderFx_boundParam - 1),
 *      i.e. g_grmShaderFx_activeInstance.
 *   2. Walk instance->paramArray[varIndex + 3] — the +3 is the RAGE
 *      convention skipping the 3-word descriptor prologue (type-id,
 *      shader-index, binding-index).
 *   3. Call rage_8C48(activeInstance, paramDesc) to perform the upload.
 *   4. Compare the newly-bound context (this+16+16, i.e. +32) against
 *      g_grmShaderFx_boundContext; update if changed.
 *   5. If the upload either changed context or is targeting a different
 *      active instance than last time, publish the new instance into
 *      g_grmShaderFx_boundParam and run rage_9E70 (the descriptor-
 *      commit routine).
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmShaderFx::BindConstantSlot(int32_t varIndex) {
    auto* self = reinterpret_cast<uint8_t*>(this);

    const uint32_t activeInstance = g_grmShaderFx_activeInstance;
    // paramArray pointer lives at +516 of the active instance.
    const uint32_t paramArrayVA =
        *reinterpret_cast<const uint32_t*>(
            reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(activeInstance)) + 516);
    const uint32_t paramDesc =
        reinterpret_cast<const uint32_t*>(
            static_cast<uintptr_t>(paramArrayVA))[varIndex + 3];

    rage_8C48(activeInstance, paramDesc);

    // The bound-context slot lives at (this+16)+16 = this+32 in
    // PPC arithmetic.  Compare/publish against the global cache.
    uint32_t* boundCtx = reinterpret_cast<uint32_t*>(self + 32);
    const uint32_t currentCtx = *boundCtx;
    const uint32_t nextCtx    = g_grmShaderFx_boundContext;

    bool contextChanged = false;
    if (currentCtx != nextCtx) {
        *boundCtx = nextCtx;
        contextChanged = true;
    }

    // Short-circuit: skip the commit if nothing changed AND the bound
    // instance already matches the live one.  Otherwise publish and
    // commit through rage_9E70.
    const uint32_t liveInstance = g_grmShaderFx_activeInstance;
    if (!contextChanged && g_grmShaderFx_boundParam == liveInstance) {
        return;
    }
    g_grmShaderFx_boundParam = liveInstance;
    rage_9E70(liveInstance);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::ResetConstantState                     [vtable slot 9]
 * @ 0x820EF9C8 | size: 0x1C (28 bytes)
 *
 * Snapshots the constant-set high-water mark into the standby slot and
 * clears it.  Accesses two fields inside the current active instance:
 *   +532 : live high-water counter
 *   +540 : standby slot (receives the pre-clear snapshot)
 *
 * Used by the render pipeline at the start of every pass that wants
 * to re-upload its parameter set from scratch.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmShaderFx::ResetConstantState() {
    const uint32_t instance = g_grmShaderFx_activeInstance;
    auto* instanceBytes =
        reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(instance));
    uint32_t* liveCounter    = reinterpret_cast<uint32_t*>(instanceBytes + 532);
    uint32_t* standbyCounter = reinterpret_cast<uint32_t*>(instanceBytes + 540);
    const uint32_t snapshot = *liveCounter;
    *liveCounter = 0;
    *standbyCounter = snapshot;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::GetTypeClassId                         [vtable slot 10]
 * @ 0x820EF9E8 | size: 0x1C (28 bytes)
 *
 * Returns the RTTI-style class-id cached at the head of this shader's
 * registry entry (first dword).  Registry lookup pattern:
 *   shaderId = *(uint16*)(this + 6)                (rotlwi r9,r10,2 ≡ *4)
 *   entry    = g_grmShaderFx_registry[shaderId]
 *   return  *(uint32_t*)entry
 * ═══════════════════════════════════════════════════════════════════════════ */
uint32_t grmShaderFx::GetTypeClassId() {
    const uint16_t shaderId =
        *reinterpret_cast<const uint16_t*>(
            reinterpret_cast<const uint8_t*>(this) + 6);
    const uint32_t entry = grmShaderFx_registryEntry(shaderId);
    return *reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(entry));
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::GetTechniquePass                       [vtable slot 11]
 * @ 0x820EF060 | size: 0x64 (100 bytes)
 *
 * Returns the callable pointer for pass `passIndex` of the currently-
 * active variant.  The lookup walks:
 *
 *   variant    = resolveVariantIndex()                 (same as Dispatch)
 *   techTable  = this->techniqueData                   (this+64)
 *   passDesc   = techTable[variant * 4 + passIndex]
 *   device     = *(this+16)->activeDevice              (offset +512)
 *   slot       = passDesc.shaderSlotId                 (16-bit at +0)
 *   entry      = device->slotTable[slot]
 *   return entry->callable                             (offset +4)
 * ═══════════════════════════════════════════════════════════════════════════ */
uint32_t grmShaderFx::GetTechniquePass(int32_t passIndex) {
    auto* self = reinterpret_cast<const uint8_t*>(this);

    const uint32_t variantIndex = grmShaderFx_resolveVariantIndex();
    const uint32_t* techniqueData =
        *reinterpret_cast<const uint32_t* const*>(self + 64);
    const uint32_t passDesc =
        techniqueData[(variantIndex << 2) + static_cast<uint32_t>(passIndex)];

    // device is *(this + 16); its slotTable is at +512.
    const uint32_t effectObj =
        *reinterpret_cast<const uint32_t*>(self + 16);
    const uint32_t deviceSlotTable = *reinterpret_cast<const uint32_t*>(
        reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(effectObj)) + 512);

    // passDesc is a 32-bit "(shaderSlotId << 16) | (...)" packed word;
    // the slot index is bits 16..29 and is byte-scaled (rlwinm r5,r6,16,16,29).
    const uint32_t slotByteOffset = (passDesc >> 14) & 0xFFFC;
    const uint32_t slotEntry = *reinterpret_cast<const uint32_t*>(
        reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(deviceSlotTable)) + slotByteOffset);

    // Return the +4 callable field.
    return *reinterpret_cast<const uint32_t*>(
        reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(slotEntry)) + 4);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::GetVariableCount                       [vtable slot 12]
 * @ 0x820F0710 | size: 0x1C (28 bytes)
 *
 * Identical registry lookup to GetTypeClassId, but reads the uint16
 * variable-count stored at offset +36 of the selected registry entry.
 * ═══════════════════════════════════════════════════════════════════════════ */
uint16_t grmShaderFx::GetVariableCount() {
    const uint16_t shaderId =
        *reinterpret_cast<const uint16_t*>(
            reinterpret_cast<const uint8_t*>(this) + 6);
    const uint32_t entry = grmShaderFx_registryEntry(shaderId);
    return *reinterpret_cast<const uint16_t*>(
        reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(entry)) + 36);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::CopyVariableDescriptor                 [vtable slot 13]
 * @ 0x820F0738 | size: 0x44 (68 bytes)
 *
 * Copies the 56-byte variable descriptor for `varIndex` out of the
 * registry entry's variable array (ptr at registry_entry + 32).  The
 * hand-rolled PPC loop moves 14 dwords; we emit the same via a plain
 * 14-iteration dword copy so the compiler can still reduce it.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmShaderFx::CopyVariableDescriptor(int32_t varIndex,
                                         uint32_t* destBuffer) {
    const uint16_t shaderId =
        *reinterpret_cast<const uint16_t*>(
            reinterpret_cast<const uint8_t*>(this) + 6);
    const uint32_t entry = grmShaderFx_registryEntry(shaderId);
    const uint32_t variableArrayVA = *reinterpret_cast<const uint32_t*>(
        reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(entry)) + 32);

    const uint32_t* source =
        reinterpret_cast<const uint32_t*>(
            reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(variableArrayVA))
            + static_cast<uint32_t>(varIndex) * 56);

    for (int i = 0; i < 14; ++i) {
        destBuffer[i] = source[i];
    }
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::GetAuxData                             [vtable slot 16]
 * @ 0x820F0730 | size: 0x08 (8 bytes)
 *
 * Trivial getter: returns the 32-bit auxiliary-data pointer cached at
 * offset +60.  Used by material-binding code to reach the shader's
 * extended render-state block without widening the hot vtable.
 * ═══════════════════════════════════════════════════════════════════════════ */
uint32_t grmShaderFx::GetAuxData() {
    return *reinterpret_cast<const uint32_t*>(
        reinterpret_cast<const uint8_t*>(this) + 60);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * grmShaderFx::ReleaseResources                       [vtable slot 17]
 * @ 0x820F0578 | size: 0x7C (124 bytes)
 *
 * Full teardown of owned resources before chaining to the base-class
 * destructor (rage_F340).  Owned state:
 *   +16  effect instance        — destroyed via rage_5BF8
 *   +20  handle table           — released via rage_free_00C0
 *   +16  re-walked to run rage_A1F8 against the registry entry
 *   +64  technique-table buffer — released via rage_free_00C0
 *   +68  uint16 handle-count    — zeroed
 *   +70  uint16 handle-capacity — zeroed
 *
 * After this returns, the base grmShader slice is in a safe state for
 * rage_F340 to finish the chain.
 * ═══════════════════════════════════════════════════════════════════════════ */
void grmShaderFx::ReleaseResources() {
    auto* self = reinterpret_cast<uint8_t*>(this);

    // +16: effect instance (the rage_5BF8 destructor).
    uint32_t* effectSlot = reinterpret_cast<uint32_t*>(self + 16);
    if (*effectSlot != 0) {
        rage_5BF8(*effectSlot);
        *effectSlot = 0;
    }

    // +20: handle table — unconditionally freed (guest free() tolerates null).
    uint32_t* handleTableSlot = reinterpret_cast<uint32_t*>(self + 20);
    rage_free_00C0(*handleTableSlot);
    *handleTableSlot = 0;

    // Walk the registry entry (via shaderId at +6) and release
    // per-variable slots.  First arg is this+16 (effect slot group),
    // second arg is the registry entry's variable-array header at +8.
    const uint16_t shaderId =
        *reinterpret_cast<const uint16_t*>(self + 6);
    const uint32_t entry = grmShaderFx_registryEntry(shaderId);
    const uint32_t variableArrayHeaderVA =
        static_cast<uint32_t>(entry + 8);
    rage_A1F8(reinterpret_cast<uintptr_t>(self + 16),
              variableArrayHeaderVA);

    // +64: technique-table buffer.
    uint32_t* techniqueTableSlot = reinterpret_cast<uint32_t*>(self + 64);
    rage_free_00C0(*techniqueTableSlot);
    *techniqueTableSlot = 0;

    // +68 / +70: handle-count / handle-capacity (packed 16-bit pair).
    *reinterpret_cast<uint16_t*>(self + 68) = 0;
    *reinterpret_cast<uint16_t*>(self + 70) = 0;

    // Chain to the base grmShader destructor body.
    rage_F340(reinterpret_cast<uintptr_t>(this));
}

} // namespace rage
