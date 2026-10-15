/**
 * player_data.cpp — Player data the image defines
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


// @ 0x8202C4E4 (.rdata)
extern "C" const float g_kBoundsLower36 = 0.800000012f;

// @ 0x8202CFF4 (.rdata)
extern "C" alignas(16) const float g_kBoundsUpper32[2] = {1.25f, 2.00501254e-05f};

// @ 0x8202D108 (.rdata)
extern "C" const float g_kFloatConst_D108 = 1.0f;

// @ 0x8202D10C (.rdata)
extern "C" const float g_kFloatConst_D10C = 0.5f;

// @ 0x8202D110 (.rdata)
extern "C" const float g_kFloatConst_D110 = 0.0f;

// @ 0x8202D118 (.rdata)
extern "C" alignas(16) const float g_kPercentScale[3] = {100.0f, 0.0f, 1.0f};

// @ 0x8202D168 (.rdata)
extern "C" const float g_kFloatConst_D168 = 0.00100000005f;

// @ 0x82079AD4 (.rdata)
extern "C" const float g_kSwingDisplay0 = -3.40282347e+38f;

// @ 0x82079AD8 (.rdata)
extern "C" const float g_kSwingDisplay1 = 3.40282347e+38f;

// @ 0x82079B00 (.rdata)
extern "C" const double g_kDoubleConst_79B00 = 0.0;

// @ 0x82079B08 (.rdata)
extern "C" const double g_kDoubleConst_79B08 = 1.0;

// @ 0x82079B20 (.rdata)
extern "C" const float g_kBoundsLower32 = 0.99000001f;

// @ 0x82079B24 (.rdata)
extern "C" const float g_kBoundsUpper36 = 0.889999986f;

// @ 0x82079BAC (.rdata)
extern "C" const float g_kFloatConst_79BAC = 0.0174532924f;

// @ 0x82079BB8 (.rdata)
extern "C" const float g_kFloatConst_79BB8 = 0.0333333351f;

// @ 0x82079C04 (.rdata)
extern "C" const float g_kFloatConst_79C04 = -1000.0f;

// @ 0x82079CD8 (.rdata)
extern "C" const float g_kFloatConst_79CD8 = 0.449999988f;

// @ 0x82079D00 (.rdata)
extern "C" const double g_kDoubleConst_79D00 = 1000.0;

// @ 0x82079D10 (.rdata)
extern "C" const double g_kDoubleConst_79D10 = -1.0;

// @ 0x82079E68 (.rdata)
extern "C" const float g_kFloatConst_79E68 = 1.1920929e-07f;

// @ 0x82079EC8 (.rdata)
extern "C" const double g_kDoubleConst_79EC8 = -1000.0;

// @ 0x82079FF8 (.rdata)
extern "C" const float g_kFloatConst_79FF8 = 0.161290318f;

// @ 0x82079FFC (.rdata)
extern "C" const float g_kFloatConst_79FFC = 0.0322580636f;

// @ 0x825C7598 (.data) — a 8-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) float lbl_825C7598[4] = {7.0f, 10.0f, 0.0f, 0.0f};

// @ 0x825C7600 (.data) — a 12-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) float lbl_825C7600[6] = {-11.8500004f, -11.8500004f, -11.8500004f, 0.0f, 0.0f, 0.0f};

// @ 0x825C80FC (.data) — a 8-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) float g_kSwingTargetConst[4] = {0.25999999f, 0.75f, 0.0f, 0.0f};

// @ 0x825C8A50 (.data) — a 16-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) float g_kContactScale1[8] = {10.0f, 1.0f, 2.0f, 1.40129846e-45f, 0.0f, 0.0f, 0.0f, 0.0f};

// @ 0x825CA2C8 (.data)
extern "C" alignas(16) uint32_t g_rngState[2] = {0x1u, 0x10001u};

// @ 0x825CAEC0 (.data)
extern "C" float g_kTransitionStep = 0.0166666675f;

// @ 0x825CAF0C (.data)
extern "C" float lbl_825CAF0C = 0.0166666675f;

// @ 0x825CAF7C (.data)
extern "C" float g_swingSlotGridDefault = 0.00100000005f;

// @ 0x825CB3C0 (.data)
extern "C" uint8_t g_replayStateData[20] = {0x82, 0x03, 0xCD, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x825CBCE4 (.data)
extern "C" float g_ballGravity = -9.80000019f;

// @ 0x8260642F (.data)
extern "C" uint8_t lbl_8260642F = 0x0u;

// @ 0x82606720 (.data)
extern "C" alignas(16) uint8_t g_mirrorBuffer[32] = {};

// @ 0x82606740 (.data)
extern "C" alignas(16) float g_identityVector[4] = {0.0f, 0.0f, 0.0f, 0.0f};
TT_DATA_ALIAS("g_identityVec", "g_identityVector");
TT_DATA_ALIAS("g_phBoundAABBTemplate", "g_identityVector");

// @ 0x82607210 (.data) — a 16-byte object in the image (zero); room for host pointer widths
extern "C" alignas(16) uint8_t g_kCourtBoxOuterMin[32] = {};

// @ 0x82607220 (.data) — a 16-byte object in the image (zero); room for host pointer widths
extern "C" alignas(16) uint8_t g_kCourtBoxInnerMin[32] = {};

// @ 0x82607230 (.data) — a 16-byte object in the image (zero); room for host pointer widths
extern "C" alignas(16) uint8_t g_kCourtBoxInnerMax[32] = {};

// @ 0x82607240 (.data) — a 16-byte object in the image (zero); room for host pointer widths
extern "C" alignas(16) uint8_t g_kCourtBoxOuterMax[32] = {};

// @ 0x8261A3D0 (.data)
extern "C" alignas(16) uint8_t g_ballSplashArray[832] = {};
TT_DATA_ALIAS("g_playerDataArray2", "g_ballSplashArray");

// @ 0x8271A304 (.data)
extern "C" void* g_pGlobalClock = nullptr;

// @ 0x8271A31C (.data)
extern "C" void* g_pPlayerRecords = nullptr;
