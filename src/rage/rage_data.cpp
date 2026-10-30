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

// Shared image state: definitions belong here, never in a lifted code TU.
// @ 0x82602808 / 0x8260280C / 0x82602810 — start, end, current (in that order)
extern "C" uint32_t g_miniheapStart = 0;    // @ 0x82602808
extern "C" uint32_t g_miniheapEnd = 0;      // @ 0x8260280C
extern "C" uint32_t g_miniheapCurrent = 0;  // @ 0x82602810

uint32_t g_activeLoggingAllocatorCount = 0;  // @ 0x825EBD20
extern "C" uint8_t g_sysMemDebugFillFlag = 0;  // @ 0x8260642D

namespace rage {
uint32_t g_sysMemAllocationTag = 0;     // @ 0x825EBCE4
uint32_t g_sysMemAllocatorInitLock = 0;  // @ 0x825EBCF8
int32_t g_swfPointerX = 0;              // @ 0x825F312C
int32_t g_swfPointerY = 0;              // @ 0x825F3138
void* g_swfGlobalObject = nullptr;      // @ 0x82602818
void* g_currentSwfContext = nullptr;    // @ 0x8260281C
void* g_swfRenderCallbackOwner = nullptr; // @ 0x82602814
uint16_t g_swfMaskEndDepth = 0;          // @ 0x826066CC
void* g_swfRootObject = nullptr;        // @ 0x82602828
void* g_swfGlobalScope = nullptr;       // @ 0x8260282C
void* g_swfSlotObject = nullptr;        // @ 0x82604848
int32_t g_swfContextStackCount = 0;     // @ 0x8260484C
int32_t g_swfContextStackFocusIndex = 0; // @ 0x82604C64
void* g_swfContextStack[32] = {};       // @ 0x82604C68
// Code takes these objects' addresses, rather than loading pointer slots.
alignas(16) uint8_t g_swfStringBuffer[1024] = {};  // @ 0x82604850
void* g_vtable_swfSCRIPTOBJECT[17] = {};          // @ 0x82074D14
uint32_t g_swfCallDepth = 0;                     // @ 0x82604D1C
uint32_t g_swfValueStack[192] = {};              // @ 0x82715C98 (768 bytes)
float g_swfFrameScale = 0.0009765625f;           // @ 0x82079B90
}
TT_DATA_ALIAS("g_ambientStreamFlags", "g_grmShaderFx_flushRequired");  // @ 0x825EBB1C

extern "C" void* g_hsmHelperContext = nullptr;     // @ 0x8271A7C0
extern "C" void* g_hsmHelperNameSource = nullptr;  // @ 0x8271A7C4
