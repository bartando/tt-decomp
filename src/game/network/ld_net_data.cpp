/**
 * ld_net_data.cpp — network / match / creature / misc data the image defines
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Globals and constants that code in these subsystems references but nothing
 * defined. Each sits at the address in its comment; constants take their
 * value from the game image, pointers start null (the image's values are
 * PPC addresses), and vtables are null-filled tables of the original's size.
 * Names that the code uses for the same address are aliases of one object.
 */

#include <cstdint>
#include "link/tt_alias.h"


// ── .rdata constants ───────────────────────────────────────────────────────

// @ 0x8202D110 (.rdata)
extern "C" const float g_netSyncTimeout = 0.0f;
TT_DATA_ALIAS("g_playerStopDefaultFloat", "g_netSyncTimeout");

// @ 0x8205A594 (.rdata) — rage::fiTokenizer; 40 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_fiTokenizer_vtable[40] = {};

// @ 0x8203338C (.rdata) — RTTI calls it sgNode; plrPropMgr's dtor drops to it. 31 slots, null in the port
extern "C" void* const atSingleton_plrPropMgr_vtable[31] = {};

// @ 0x8206C394 (.rdata) — RTTI: LogicNetworkClient; 22 slots, null in the port
extern "C" void* const SpectatorMessage_vtable[22] = {};

// @ 0x8206C3F4 (.rdata) — RTTI: NetworkClient; 9 slots, null in the port
extern "C" void* const SinglesNetworkClient_intermediate_vtable[9] = {};

// @ 0x8206F500 (.rdata) — RTTI: HitDataMessage; 8 slots, null in the port
extern "C" void* const NetworkStats_vtable[8] = {};

// 0x8207166C (FloatAverager_vtable_4) is aliased in globals.c.

// @ 0x8207169C (.rdata)
extern "C" const char g_plrProp_propTypeName[] = "plrPropMgr";

// @ 0x82079AD4 (.rdata) — -FLT_MAX
extern "C" const float lbl_82079AD4 = -3.40282347e+38f;
TT_DATA_ALIAS("g_pongNetMaxFloatInit_9ADC", "lbl_82079AD4");
TT_DATA_ALIAS("g_defaultTimestamp", "lbl_82079AD4");

// @ 0x82079AD8 (.rdata) — FLT_MAX
extern "C" const float g_defaultTimestampAlt = 3.40282347e+38f;

// @ 0x82079B20 (.rdata)
extern "C" const float g_blendCurveScale = 0.99000001f;

// @ 0x820695BC (.rdata)
extern "C" const char lbl_820695BC[] = "XONLINE_E_FEEDBACK_CANNOT_LOG";


// ── .data ─────────────────────────────────────────────────────────────────

// 0x825C5938 (g_defaultTimeout, g_fDefaultTimer) is aliased in char_view_data.cpp.

// @ 0x825CAEB8 (.data) — the rage::sysTimeManager instance (match_data.cpp's
// g_sysTimeManager covers only its first 16 bytes). The image's words, the
// vtable at +0 nulled; readers index it by PPC offsets (+0x54: 1/60 s tick).
extern "C" alignas(16) uint32_t g_hudShell_UpdateBlock[24] = {
    0x00000000u, 0x00000000u, 0x3C888889u, 0x42700000u,
    0x00000000u, 0x00000000u, 0x42700000u, 0x3C888889u,
    0x3DCCCCCDu, 0x38D1B717u, 0x00000000u, 0x00000001u,
    0x01000000u, 0x00000000u, 0x00000000u, 0x00000000u,
    0x00000000u, 0x00000000u, 0x00000000u, 0x3C888889u,
    0x3F800000u, 0x3C888889u, 0x3C888889u, 0x00000000u,
};

// @ 0x825D129C (.data) — a 12-byte holder in the image (vtable 0x820702AC, then
// zeros): pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t g_holderInstance_129C[24] = {};

// @ 0x825D12B4 (.data) — as above, vtable 0x820702C0
extern "C" alignas(16) uint8_t g_holderInstance_AudioRefCount[24] = {};

// @ 0x825D1638 (.data) — RequestDataMessage's type node {id = -1, name, next};
// the id is assigned at runtime, the list link by 0x82581590
extern "C" alignas(16) uint8_t g_holderInstance_MotionRangeMgr[24] = {
    0xFF, 0xFF, 0xFF, 0xFF};

// @ 0x825D1900 (.data) — EvtStart's type node {id = -1, name, next}; linked by 0x82582028
extern "C" alignas(16) uint8_t g_holderInstance_DataMgr[24] = {
    0xFF, 0xFF, 0xFF, 0xFF};

// MSVC RTTI type descriptor: vftable of type_info, spare, decorated name
struct LdRttiTypeDescriptor {
    void* pVFTable;
    void* spare;
    char  name[28];
};

// @ 0x825D4520 (.data)
extern "C" LdRttiTypeDescriptor g_typeDescriptor_phInstBehavior = {
    nullptr, nullptr, ".?AVphInstBehavior@rage@@"};

// @ 0x825D4544 (.data)
extern "C" LdRttiTypeDescriptor g_typeDescriptor_phRope = {
    nullptr, nullptr, ".?AVphRope@rage@@"};

// @ 0x825EB900 (.data) — zero in the image; covers through the pointer at +0x88
extern "C" alignas(16) uint8_t lbl_825EB900[0x90] = {};

// @ 0x826066A0 (.data) — head of the static message-holder list; runtime-initialised by the 0x8257F668 family
extern "C" uint32_t g_netMessageHolderInitHead_raw = 0u;

// @ 0x82606672 (.data)
extern "C" uint8_t g_spectatorModeEnabled = 0;

// 0x82606750 (g_zeroVec4) is aliased in creature_data.cpp.

// 0x8271A2F0 (lbl_8271A2F0) and 0x8271A7B0 (g_playerDataArray) are aliased in globals.c.

// @ 0x8271A31C (.data) — runtime-initialised pointer
extern "C" void* g_pongGameInstance = nullptr;


// No image address: the lifts' stand-in for the r13 thread block, whose +4
// holds the current allocator. Set at thread start in the original.
extern "C" alignas(16) void* g_allocator_ptr[2] = {};
