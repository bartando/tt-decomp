/**
 * grc_data.cpp — Graphics data the image defines
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Globals and constants that code in this subsystem references but nothing
 * defined. Each sits at the address in its comment; constants take their
 * value from the game image, pointers start null (the image's values are
 * PPC addresses), and vtables are null-filled tables of the original's size.
 * Names that the code uses for the same address are aliases of one object.
 */

#include <cstdint>
#include "link/tt_alias.h"


// @ 0x8202D110 (.rdata)
extern "C" const float g_grcRenderTargetDefaultLOD = 0.0f;

// @ 0x82065D10 (.rdata) — max anisotropy (0..16) to Xenos aniso_filter encoding
extern const uint32_t g_grcAnisoFilterTable[17] = {
    0, 0, 2, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5
};

// @ 0x82035300 (.rdata)
extern "C" const char g_invalidTextureTypeMsg[61] = "Bad resource type %d in grcTextureFactoryXenon::PlaceTexture";

// @ 0x826063E8 (.data)
extern "C" void* g_grcRefCountedObjs[4] = {};

// @ 0x82606400 (.data)
extern "C" void* g_pGrcTextureFactoryString = nullptr;

// @ 0x82617E60 (.data)
extern "C" void* g_grcRenderObjects[2] = {};

uint32_t g_ambientStreamSlotCap = 0;  // @ 0x825C8F54
uint32_t g_ambientMappedSlot = 0;     // @ 0x825EBB84
uint32_t g_ambientCurSlot = 0;        // @ 0x825EBBDC

// Shared normalized color clamp bounds from the image.
extern const float g_colorClampMin = 0.0f; // @ 0x8202D110
extern const float g_colorClampMax = 1.0f; // @ 0x8202D108

// @ 0x8260640C (.data) — use the resource locking path for CPU mappings
extern "C" uint8_t g_grcUseResourceLocks = 0;

namespace rage {
// @ 0x82606562 (.data) — suppress resource unlock while endian data is dirty
uint8_t g_bTextureEndianDirty = 0;
}
