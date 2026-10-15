/**
 * misc_data.cpp — Misc game code data the image defines
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


// @ 0x8202CFE8 (.rdata)
extern "C" alignas(16) const float lbl_8202CFE8[2] = {0.100000001f, -0.0981747732f};

// @ 0x8202D110 (.rdata)
extern "C" const float lbl_8202D110 = 0.0f;

// @ 0x820381C4 (.rdata) — 15 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAnimCamOrientation_vtable[15] = {};

// @ 0x8203821C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAnimCamFov_vtable[22] = {};

// @ 0x82038274 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAnimCamFStop_vtable[22] = {};

// @ 0x820382CC (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAnimDuration_vtable[22] = {};

// @ 0x82038324 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAnimBonePosition_vtable[22] = {};

// @ 0x8203837C (.rdata) — 20 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAnimBoneOrientation_vtable[20] = {};

// @ 0x820411FC (.rdata) — 26 slots of PPC code addresses in the image, null in the port
extern "C" void* const gdDrillSoftShotData_vtable[26] = {};

// @ 0x82053A6C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAdd_vtable[22] = {};

// @ 0x82053AC4 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmSubtract_vtable[22] = {};

// @ 0x82053B1C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmMultiply_vtable[22] = {};

// @ 0x82053B74 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmDivide_vtable[22] = {};

// @ 0x82053BCC (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmModulo_vtable[22] = {};

// @ 0x82053C24 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmNegate_vtable[22] = {};

// @ 0x82053C7C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmSine_vtable[22] = {};

// @ 0x82053CD4 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmCosine_vtable[22] = {};

// @ 0x82053D2C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmArcCosine_vtable[22] = {};

// @ 0x82053D84 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmTangent_vtable[22] = {};

// @ 0x82053DDC (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmArcTangent_vtable[22] = {};

// @ 0x82053E34 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmInverse_vtable[22] = {};

// @ 0x82053E8C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAbs_vtable[22] = {};

// @ 0x82053EE4 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmSign_vtable[22] = {};

// @ 0x82053F3C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmMax_vtable[22] = {};

// @ 0x82053F94 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmMin_vtable[22] = {};

// @ 0x82053FEC (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmLerp_vtable[22] = {};

// @ 0x82054044 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAngleLerp_vtable[22] = {};

// @ 0x8205409C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmRange_vtable[22] = {};

// @ 0x820540F4 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmClamp_vtable[22] = {};

// @ 0x8205414C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAbsAngleDiff_vtable[22] = {};

// @ 0x820541A4 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAngleDiff_vtable[22] = {};

// @ 0x820541FC (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmClampRange_vtable[22] = {};

// @ 0x82054254 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmSlowIn_vtable[22] = {};

// @ 0x820542AC (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmSlowOut_vtable[22] = {};

// @ 0x82054304 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmSlowInOut_vtable[22] = {};

// @ 0x82054464 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmNoise_vtable[22] = {};

// @ 0x820544BC (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmVectorNoise_vtable[22] = {};

// @ 0x82054514 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmSphericalNoise_vtable[22] = {};

// @ 0x8205456C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmGNoise_vtable[22] = {};

// @ 0x820545C4 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmVectorGNoise_vtable[22] = {};

// @ 0x8205461C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmEquals_vtable[22] = {};

// @ 0x82054674 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmGreaterThan_vtable[22] = {};

// @ 0x820546CC (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmLessThan_vtable[22] = {};

// @ 0x82054724 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmOr_vtable[22] = {};

// @ 0x8205477C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmXor_vtable[22] = {};

// @ 0x820547D4 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmAnd_vtable[22] = {};

// @ 0x8205482C (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmNot_vtable[22] = {};

// @ 0x82054884 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmDifferential_vtable[22] = {};

// @ 0x82054BF4 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmInfo_vtable[22] = {};

// @ 0x82054CA4 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmDevArg_vtable[22] = {};

// @ 0x82054D54 (.rdata) — 22 slots of PPC code addresses in the image, null in the port
extern "C" void* const rage_cmLocalRestart_vtable[22] = {};

// @ 0x820681A0 (.rdata)
extern "C" const char lbl_820681A0[37] = "Reset() called while read is pending";

// @ 0x8206A824 (.rdata)
extern "C" const char lbl_8206A824[12] = "jdg_sit_stn";

// @ 0x8206A888 (.rdata)
extern "C" const char lbl_8206A888[12] = "jdg_pnt_lft";

// @ 0x8206A894 (.rdata)
extern "C" const char lbl_8206A894[12] = "jdg_pnt_rgt";

// @ 0x825C40FF (.data) — a 57-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) uint8_t lbl_825C40FF[114] = {0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

// @ 0x82606404 (.data)
extern "C" void* g_sda_6404 = nullptr;

// @ 0x8260660D (.data)
extern "C" uint8_t g_sda_660D = 0x0u;
