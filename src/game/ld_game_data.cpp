/**
 * ld_game_data.cpp — game data the image defines (ball, player, xam users)
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


// ── .rdata ──────────────────────────────────────────────────────────────────

// @ 0x8202D168 (.rdata) — not one object: xe_0780 (0x820F0780) loads three
// separate constants, 0x8202D110, 0x8202D108 and 0x8202D168, into +0x24/+0x28/+0x2C
extern "C" const float g_float_values[3] = {0.0f, 1.0f, 0.00100000005f};

// @ 0x8202F5A8 (.rdata) — rage::grmModelFactory, 3 slots
extern "C" void* const vtable_rage_grmModelFactory[3] = {};

// @ 0x82030154 (.rdata) — gmLogicNode, 32 slots; xe_1E48 stores its address at +0x00
extern "C" void* const lbl_82020120_vtable_word[32] = {};

// @ 0x820301DC (.rdata) — gmLogicNode's second vtable, 2 slots; stored at +0x10
extern "C" void* const lbl_820201D8_vtable_word[2] = {};

// @ 0x82035570 (.rdata) — rage::audControlMgr, 6 slots
extern "C" void* const audVoice_vtable_word[6] = {};

// @ 0x82079CE8 (.rdata) — lfs; the lower clamp of ClampMovementToCourtBounds
extern "C" const float g_kCourtMinDelta = -5.0f;

// @ 0x82079CF8 (.rdata) — lfd
extern "C" const double g_kCourtMaxDelta = 5.0;

// @ 0x8207A320 (.rdata)
extern "C" const float lbl_8207A320 = -0.0199999996f;


// ── .data ───────────────────────────────────────────────────────────────────

// @ 0x825C76DC (.data) — 3 columns, indexed slot * 3 + column
extern "C" float g_kSlotSpeedLookup[3] = {5.0f, 10.0f, 15.0f};

// @ 0x825C8138 (.data)
extern "C" const float lbl_825C8138 = 0.0199999996f;

// Command-line option records (sysParam), 20 bytes each in the image:
// name, value, preset, next, 0. The name pointers are nulled; each record's
// option is in its comment. Registered onto 0x825EBCF4 by 0x8257B940..0x8257BA40.

// @ 0x825C9DD4 (.data) — "netassets"
extern "C" alignas(16) uint8_t g_staticInit_0[40] = {};

// @ 0x825C9DE8 (.data) — "path"
extern "C" alignas(16) uint8_t g_staticInit_1[40] = {};

// @ 0x825C9DFC (.data) — "fast"
extern "C" alignas(16) uint8_t g_staticInit_2[40] = {};

// @ 0x825C9E10 (.data) — "singlebufferverts"
extern "C" alignas(16) uint8_t g_staticInit_3[40] = {};

// @ 0x825C9E24 (.data) — "noclothnet"
extern "C" alignas(16) uint8_t g_staticInit_4[40] = {};

// @ 0x825C9E38 (.data) — "cfgPlatform"
extern "C" alignas(16) uint8_t g_staticInit_5[40] = {};

// @ 0x825C9E4C (.data) — "cfgBuild"
extern "C" alignas(16) uint8_t g_staticInit_6[40] = {};

// @ 0x825C9E60 (.data) — "cfgOutput"
extern "C" alignas(16) uint8_t g_staticInit_7[40] = {};

// @ 0x825C9E74 (.data) — "nodbcb"
extern "C" alignas(16) uint8_t g_staticInit_8[40] = {};

// @ 0x825CA0F0 (.data) — "nomotionblur"; xe_D6F8 tests its value word (+4)
extern "C" alignas(16) uint32_t g_system_flags[10] = {};

// @ 0x825CB7C0 (.data)
extern "C" alignas(16) const float lbl_825CB7C0[4] = {1.0f, 1.0f, 1.0f, 0.0f};

// @ 0x825CB7D0 (.data)
extern "C" alignas(16) const float lbl_825CB7D0[4] = {0.5f, 0.5f, 0.5f, 0.0f};

namespace {
struct AssetFolderStackStorage {
    uint8_t head[0x600];
    int32_t folderDepth;  // +0x600
    int32_t field604;     // +0x604
    uint8_t room[0x608];  // host pointer widths
};
}  // namespace

// @ 0x825D0080 (.data) — a 0x608-byte object; the image's only nonzero word is +0x604 = 1
extern "C" alignas(16) AssetFolderStackStorage g_assetFolderStack = {{}, 0, 1, {}};
TT_DATA_ALIAS("g_fiAssetManager", "g_assetFolderStack");

// @ 0x825D2CB8 (.data) — a 28-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t g_typeDescriptor_phInst[56] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2E, 0x3F, 0x41, 0x56, 0x70, 0x68, 0x49, 0x6E, 0x73, 0x74, 0x40, 0x72, 0x61, 0x67, 0x65, 0x40, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x825D2CD4 (.data) — a 32-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t g_typeDescriptor_pongBallInstance[64] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2E, 0x3F, 0x41, 0x56, 0x70, 0x6F, 0x6E, 0x67, 0x42, 0x61, 0x6C, 0x6C, 0x49, 0x6E, 0x73, 0x74, 0x61, 0x6E, 0x63, 0x65, 0x40, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x825D4C80 (.data) — 0x80 >> n
extern "C" const uint8_t lbl_825D4C80[8] = {0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01};

// @ 0x825EB2FC (.data) — runtime-initialised by 0x822BDC80
extern "C" void* lbl_825EB2FC = nullptr;

// @ 0x82606578 (.data)
extern "C" int32_t g_currentInputSlot = 0;

// @ 0x8260648D (.data) — runtime-initialised by pongBallHitData_vfn_21 (0x821D6608)
extern "C" uint8_t g_pongBallHitDataEnableFlag = 0;

// @ 0x8260656D (.data)
extern "C" uint8_t lbl_8260656D = 0;

// @ 0x82619BF0 (.data) — zero in the image
extern "C" alignas(16) float lbl_82619BF0[4] = {};

// @ 0x8271A2E8 (.data) — the match clock block (+0x30 = now, seconds)
extern "C" void* g_pongMatchTiming = nullptr;
TT_DATA_ALIAS("g_atSingleton_2940_ptr", "g_pongMatchTiming");
