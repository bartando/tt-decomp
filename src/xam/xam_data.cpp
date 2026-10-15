/**
 * xam_data.cpp — XAM layer data the image defines
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


// @ 0x820282EC (.rdata) — 26 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_rage_xmlNodeStruct[26] = {};

// @ 0x8202D108 (.rdata)
extern "C" const float g_float_zero = 1.0f;

// @ 0x8202D110 (.rdata)
extern "C" void* const g_float_one_ptr = nullptr;

// @ 0x8202EB64 (.rdata) — 24 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_pcrEmoteData[24] = {};

// @ 0x82043300 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_hitTipData[3] = {};

// @ 0x8204330C (.rdata) — 25 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_hitTipData_base[25] = {};

// @ 0x82043398 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_serveTipData[3] = {};

// @ 0x820433A4 (.rdata) — 25 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_serveTipData_base[25] = {};

// @ 0x82043430 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_focusMeterTipData[3] = {};

// @ 0x8204343C (.rdata) — 25 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_focusMeterTipData_base[25] = {};

// @ 0x820434A0 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_forcedFromTableCenterTipData[3] = {};

// @ 0x820434AC (.rdata) — 25 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_forcedFromTableCenterTipData_base[25] = {};

// @ 0x82043510 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_noSoftShotsTipData[3] = {};

// @ 0x8204351C (.rdata) — 25 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_noSoftShotsTipData_base[25] = {};

// @ 0x82043580 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_tooFarFromTableTipData[3] = {};

// @ 0x8204358C (.rdata) — 25 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_tooFarFromTableTipData_base[25] = {};

// @ 0x820435F0 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_badSoftShotTipData[3] = {};

// @ 0x820435FC (.rdata) — 25 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_badSoftShotTipData_base[25] = {};

// @ 0x8204B244 (.rdata) — 26 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_gdUnlockConditionMultiBounce[26] = {};

// @ 0x82077D1C (.rdata) — 26 slots of PPC code addresses in the image, null in the port
extern "C" void* const vtable_gdCSActionCharVisibleData[26] = {};

// @ 0x8260637C (.data)
extern "C" void* g_large_buffer_ptr = nullptr;
