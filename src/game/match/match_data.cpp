/**
 * match_data.cpp — Match logic data the image defines
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


// @ 0x82032404 (.rdata) — 4 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_pongRenderable_vtable[4] = {};

// @ 0x82032414 (.rdata) — 5 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_gmPracticeTarget_vtable[5] = {};

// @ 0x82032428 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_gmPracticeTarget_pongRenderable_vtable[3] = {};

// @ 0x825C60CC (.data) — holds its own address (a type id)
extern "C" void* g_gdaiDeficitTypeId = &g_gdaiDeficitTypeId;

// @ 0x825C60D0 (.data) — holds its own address (a type id)
extern "C" void* g_gdaiLeadTypeId = &g_gdaiLeadTypeId;

// @ 0x825C9A28 (.data)
extern "C" float g_swingPracticeFadeTime = 0.5f;

// @ 0x825CA198 (.data)
extern "C" uint32_t g_practiceTargetDefaultColor = 0x3F0019EFu;

// @ 0x825CA19C (.data)
extern "C" uint32_t g_practiceTargetHitColor = 0x3FFFFF00u;

// @ 0x825D1218 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint32_t g_exitPostGameMsgClassId[6] = {0xFFFFFFFFu, 0x0u, 0x0u, 0x0u, 0x0u, 0x0u};

// @ 0x825D1224 (.data)
extern "C" char g_messagePoolInfo[5] = "\202\007\002H";
TT_DATA_ALIAS("g_holderInstance_String", "g_messagePoolInfo");

// @ 0x8260637A (.data)
extern "C" uint8_t g_swingPracticeMoveTarget = 0x0u;

// @ 0x826063AC (.data)
extern "C" int32_t g_practiceTargetNumSets = 0;

// @ 0x8271A2EC (.data)
extern "C" void* g_pReplayStateData = nullptr;
TT_DATA_ALIAS("g_cameraDataBasePtr", "g_pReplayStateData");
TT_DATA_ALIAS("g_cameraDataPtr", "g_pReplayStateData");
TT_DATA_ALIAS("lbl_8271A2EC", "g_pReplayStateData");

// @ 0x8271A2FC (.data)
extern "C" void* g_pActiveMatchContext = nullptr;

// @ 0x8271A324 (.data)
extern "C" void* lbl_8271A324 = nullptr;

// @ 0x8271A334 (.data)
extern "C" void* g_pTournamentData = nullptr;

// @ 0x8271A340 (.data)
extern "C" void* g_pNetworkStateFlags = nullptr;

// @ 0x825CAEB8 (.data) — the rage::sysTimeManager instance: vtable (null in the
// port), a word, then seconds per frame and frames per second as the image has
// them. Laid out like pong_match.cpp's sysTimeManagerView.
struct sysTimeManagerImage {
    void**   vtable;
    uint32_t field_04;
    float    frameSeconds;
    float    framesPerSecond;
};
extern "C" sysTimeManagerImage g_sysTimeManager = {nullptr, 0u, 0.0166666675f, 60.0f};
