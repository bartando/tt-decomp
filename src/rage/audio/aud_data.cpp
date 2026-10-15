/**
 * aud_data.cpp — RAGE audio data the image defines
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


// @ 0x8202D108 (.rdata)
extern "C" const float g_audVolumeClampMax = 1.0f;

// @ 0x8202D110 (.rdata)
extern "C" const float g_audGroupVolumeCeiling = 0.0f;

// @ 0x825EBCA0 (.data)
extern "C" uint8_t g_audGlobalMuteFlag = 0x0u;

// @ 0x825EBCA3 (.data)
extern "C" uint8_t g_audCtrlMgrEnableNeeded = 0x0u;

// @ 0x825EBCA8 (.data)
extern "C" void* g_audCtrlMgrStopList = nullptr;

// @ 0x8260640F (.data)
extern "C" uint8_t g_audCtrlMgrInitFlag = 0x0u;

// @ 0x82606410 (.data)
extern "C" void* g_audCtrlMgrControlPrimary = nullptr;
TT_DATA_ALIAS("g_pAudSystemContext", "g_audCtrlMgrControlPrimary");

// @ 0x82606414 (.data)
extern "C" void* g_audCtrlMgrControlListHead = nullptr;

// @ 0x82606418 (.data)
extern "C" uint8_t g_audMasterMuteFlag = 0x0u;

namespace rage {

// @ 0x825E7864 (.data)
void* g_pAudSceneSingleton = nullptr;

// @ 0x825EE224 (.data)
void* g_pAudBankEntryData = nullptr;

}  // namespace rage
