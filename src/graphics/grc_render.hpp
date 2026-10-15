/**
 * grc_render.hpp — RAGE graphics render classes
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * 9 classes (grcTextureReferenceBase + grcTextureReference are in
 * texture_reference.hpp — include that file directly; they are NOT
 * redeclared here to avoid duplicate-definition errors).
 *
 * Sources: rtti_vtable_map | vtable_layout_map | offset_cluster_map
 *          | debug_string_field_map | rtti_class_hierarchy
 */
#pragma once
#include <stdint.h>

// grcTextureReferenceBase and grcTextureReference live here:
#include "texture_reference.hpp"

namespace rage {

// ── rage::grcDirtyDisc  [vtable @ 0x82034A68] ─────────────────────────────
// Manages disc-read error handling and retry logic.
// vfn_2 (0x82151168) performs complex initialization with fiber TLS setup.
struct grcDirtyDisc {
    void** vtable;  // +0x00

    ~grcDirtyDisc();             // [0] @ 0x82151110
    void ScalarDtor(int flags);  // [1] @ 0x821511F8
    void vfn_2();                // [2] @ 0x82151168  fiber TLS init
};

// ── rage::grcRenderTargetXenon  [vtable @ 0x82035344] ─────────────────────
struct grcRenderTargetXenon {
    void** vtable;  // +0x00
    uint8_t  pad_04[16];    // +0x04
    uint16_t m_nWidth;      // +0x14
    uint16_t m_nHeight;     // +0x16
    uint8_t  pad_18[4];     // +0x18
    uint8_t  m_bColorEnabled;  // +0x1C
    uint8_t  m_bDepthEnabled;  // +0x1D
    uint8_t  m_nMSAAMode;      // +0x1E

    ~grcRenderTargetXenon();                    // [0]  @ 0x8215E750
    void vfn_7();                               // [7]  @ 0x8215EB28
    uint16_t GetWidth();                        // [8]  @ 0x8215DD58
    uint16_t GetHeight();                       // [9]  @ 0x8215DD60
    void vfn_10();                              // [10] — gap/inherited
    void SetColorChannelFlag(uint8_t flag);     // [11] — called by beginScene
    void SetDepthChannelFlag(uint8_t flag);     // [12] — called by beginScene
    void SetChannelFlags(uint8_t a, uint8_t b); // [13] @ 0x8215DD68
    void GetChannelFlags(uint8_t* a, uint8_t* b); // [14] @ 0x8215DD78
    uint8_t GetMSAAMode();                      // [15] @ 0x8215DDB0
    void SetMSAAMode(uint8_t mode);             // [16] @ 0x8215DD90
    void vfn_17();                              // [17] — gap/inherited
    void GetLODParams(float* pDist, uint32_t* pLevel); // [18] @ 0x82151250
    void vfn_19();                              // [19] — gap/inherited
    void vfn_20();                              // [20] @ 0x8215EB10
    void vfn_29();                              // [29] @ 0x8215EC28
};

// ── rage::grcSetup  [vtable @ 0x82035068] ────────────────────────────────
struct grcSetup {
    void** vtable;  // +0x00

    void ScalarDtor(int flags); // [1] @ 0x8215CC18
    void vfn_2();               // [2] @ 0x82161D40
    void vfn_3();               // [3] @ 0x82161DB8
    void vfn_4();               // [4] @ 0x8215D0D0
    void vfn_5();               // [5] @ 0x82162178
    void vfn_6();               // [6] @ 0x821620D0
    void vfn_13();              // [13] @ 0x82162420
};

// ── rage::grcTextureDictionaryReference  [vtable @ 0x8203517C] ───────────
struct grcTextureDictionaryReference {
    void** vtable;  // +0x00

    ~grcTextureDictionaryReference();  // [0] @ 0x8215DCF0
};

// ── rage::grcTextureFactory  [vtable @ 0x82034B8C] ────────────────────────
// Global singleton @ 0x825EBA20 (SDA-relative, r13 base)
struct grcTextureFactory {
    void** vtable;  // +0x00

    ~grcTextureFactory();  // [0] @ 0x82151338

    // [13] @ 0x821514E8 — texture lookup by name (hash table + strcmp)
    void vfn_13();

    // [14] @ 0x821515A0 — texture creation from .wtd file
    void vfn_14();

    // [15] @ 0x821518E8 — texture finalization / GPU upload
    void vfn_15();
};

// ── rage::grcTextureFactoryString  [vtable @ 0x82035504] ─────────────────
struct grcTextureFactoryString {
    void** vtable;  // +0x00

    void ScalarDtor(int flags); // [1] @ 0x8215FEF8
    void vfn_2();               // [2] @ 0x8215FE80
    void vfn_3();               // [3] @ 0x82160038
};

// ── rage::grcTextureFactoryXenon  [vtable @ 0x82035444] ──────────────────
// Platform-specific Xenon texture factory; handles DXT compression,
// tiling, and GPU memory management.
struct grcTextureFactoryXenon {
    void** vtable;  // +0x00

    ~grcTextureFactoryXenon();   // [0] @ 0x8215E0E0
    void ScalarDtor(int flags);  // [1] @ 0x8215E260
    void vfn_2();                // [2] @ 0x8215E180
    void vfn_3();                // [3] @ 0x8215E688
    void vfn_4();                // [4] @ 0x8215E6E0
    void vfn_5();                // [5] @ 0x8215E6F8
    void vfn_6();                // [6] @ 0x8215E308
    void vfn_7();                // [7] @ 0x8215E390
    void vfn_8();                // [8] @ 0x8215E528
    void vfn_10();               // [10] @ 0x8215FCB0
};

// ── rage::grcTextureString  [vtable @ 0x8203548C] ────────────────────────
struct grcTextureString {
    void** vtable;  // +0x00

    ~grcTextureString();  // [0] @ 0x8215FFC8
    void vfn_14();        // [14] @ 0x8215FE70
};

// ── rage::grcTextureXenon  [vtable @ 0x820353CC] ─────────────────────────
struct grcTextureXenon {
    void** vtable;      // +0x00
    uint8_t pad_04[20]; // +0x04
    uint8_t m_bColorEnabled;   // +0x18
    uint8_t m_bDepthEnabled;   // +0x19
    uint8_t pad_1A;            // +0x1A
    uint8_t m_nLodLevel;       // +0x1B
    float   m_fLodBias;        // +0x1C

    ~grcTextureXenon();                       // [0] @ 0x8215F198
    void vfn_7();                             // [7] @ 0x8215FB88
    void SetChannelFlags(uint8_t c, uint8_t d); // [13] @ 0x8215DDB8
    void GetChannelFlags(uint8_t* c, uint8_t* d); // [14] @ 0x8215DDC8
    uint8_t GetLodLevel();                    // [15] @ 0x8215DDE8
    void SetLodLevel(uint8_t level);          // [16] @ 0x8215DDE0
    void GetLodBias(float* pBiasOut);         // [18] @ 0x8215DDF0
    void vfn_20();                            // [20] @ 0x8215FC98
    void vfn_21();                            // [21] @ 0x8215FAB0
    void vfn_22();                            // [22] @ 0x8215FB70
};

} // namespace rage

// ── grcDevice GPU command submission ──────────────────────────────────────
// Non-class free functions that operate on the two flavours of grcDevice.

// grcDevice_beginScene @ 0x82305E78
// Gates scene start on render-state conditions, then dispatches to the
// attached grcRenderTargetXenon.  pDevice points to the 0x8271A81C instance.
extern void grcDevice_beginScene(void* pDevice);

// grcDevice_clear @ 0x82379290
// Advances the render-command ring, copies viewport rects into the new
// entry, executes it, then resets queue state.  pDevice points to 0x8271A320.
extern void grcDevice_clear(void* pDevice);

// grcDevice_shutdown @ 0x8214FA58
// Primary graphics device shutdown sequence with reference counting.
extern void grcDevice_shutdown(void);

// grcDevice_shutdownAlt @ 0x821540D0
// Alternate shutdown path for HUD overlay cleanup.
extern void grcDevice_shutdownAlt(void);

// grcDevice_beginGPUPass @ 0x82305D50
// Begin GPU rendering pass for this device (wraps pgStreamer).
extern void grcDevice_beginGPUPass(void* pDevice);

// pgStreamer_cancelBracket @ 0x8242C3B8
// Cancel or start a profiling bracket (mode=0: start, mode=-1: cancel).
extern void pgStreamer_cancelBracket(void* pStream, int32_t mode);

// pgStreamer_openBracket @ 0x82566DC0
// Open a profiling bracket after render target dispatch (mode=1).
extern void pgStreamer_openBracket(void* pStream, int32_t mode);

// Default viewport rectangle (16 bytes, float[4]) @ 0x8261A0C0
extern const uint8_t g_defaultViewportRect[16];
