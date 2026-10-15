/**
 * rage_data.cpp — RAGE data the image defines
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
extern "C" const float kDefaultPanY = 0.0f;

// @ 0x8202D118 (.rdata)
extern "C" alignas(16) const float kSlowOrbitMul[3] = {100.0f, 0.0f, 1.0f};

// @ 0x8202D184 (.rdata)
extern "C" const float kFastTurnMul = 2.0f;

// @ 0x8202D9A4 (.rdata)
extern "C" const float g_renderTicksToSecondsA = 2.00501254e-05f;

// @ 0x820332C4 (.rdata) — 24 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_sysMemAllocator_vtable[24] = {};

// @ 0x825C9010 (.data)
extern "C" uint32_t g_grmShaderFx_frameCounter = 0x1u;

// @ 0x825C90BC (.data) — a 220-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) float g_slowTurnMul[110] = {4.0f, 1.25f, 0.300000012f, -0.00999999978f, 4.48415509e-44f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};

// @ 0x825EAF88 (.data)
extern "C" alignas(16) uint32_t g_grmShaderFx_registry[128] = {};

// @ 0x825EBA68 (.data)
extern "C" uint32_t g_grmShaderFx_activeState = 0x0u;

// @ 0x825EBAB4 (.data)
extern "C" uint32_t g_grmShaderFx_forceResetFlag = 0x0u;

// @ 0x825EBB1C (.data)
extern "C" uint32_t g_grmShaderFx_flushRequired = 0x0u;

// @ 0x825EBC3C (.data)
extern "C" void* g_debugFont = nullptr;

// @ 0x825EBC4C (.data)
extern "C" uint32_t g_grmShaderFx_activeInstance = 0x0u;

// @ 0x825EBC50 (.data)
extern "C" uint32_t g_grmShaderFx_boundParam = 0x0u;

// @ 0x82606374 (.data)
extern "C" void* g_grmShaderFactory_instance = nullptr;

// @ 0x8271A320 (.data)
extern "C" void* g_pGrcDevice_clear = nullptr;
TT_DATA_ALIAS("g_pMatchResultData", "g_pGrcDevice_clear");

// @ 0x82037494 (.rdata) — datParserRecord's vtable, 3 slots of PPC code
// addresses in the image, null in the port. datParser_AddField stores it.
extern "C" void* const datParserRecord_vtable[3] = {};

// @ 0x825F5AA8 (.data) — the TLS slot of the resource being placed (0 until
// datResource_PointerFixup first allocates it)
extern "C" uint32_t g_datResourceTlsSlot = 0x0u;
