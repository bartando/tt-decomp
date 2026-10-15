/**
 * camera_data.cpp — Camera data the image defines
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
extern "C" const float g_cameraOffsetDelta = 1.0f;

// @ 0x8202D110 (.rdata)
extern "C" const float g_cameraSampleInitFloat2 = 0.0f;

// @ 0x8202D168 (.rdata)
extern "C" const float g_cameraTransitionOffset = 0.00100000005f;

// @ 0x82032868 (.rdata)
extern "C" const char kCamViewCS_TypeName[5] = "tune";

// @ 0x820362F8 (.rdata)
extern "C" const char kCamViewCS_DebugLabel[10] = "camViewCS";

// @ 0x82036304 (.rdata)
extern "C" const char kCamViewCS_UseGlobalClip[14] = "UseGlobalClip";

// @ 0x82036314 (.rdata)
extern "C" const char kCamViewCS_ClipNear[10] = "Clip Near";

// @ 0x82036320 (.rdata)
extern "C" const char kCamViewCS_ClipFar[9] = "Clip Far";

// @ 0x8204911C (.rdata) — 2 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_cameraSampleVtable[2] = {};

// @ 0x82079B4C (.rdata)
extern "C" const float g_cameraSampleInitFloat1 = 99999.0f;

// @ 0x82606419 (.data)
extern "C" uint8_t g_camMachineSignal = 0x0u;

// @ 0x82606420 (.data)
extern "C" uint32_t g_camMachineRecord = 0x0u;

// @ 0x826064BC (.data)
extern "C" float g_cameraTransitionTime = 0.0f;
TT_DATA_ALIAS("g_cameraLerpValue", "g_cameraTransitionTime");

// @ 0x826064C0 (.data)
extern "C" uint32_t g_cameraTransitionState = 0x0u;

// @ 0x826064C8 (.data)
extern "C" float g_cineSampleInterval = 0.0f;

// @ 0x82619AD0 (.data) — a 16-byte object in the image (zero); room for host pointer widths
extern "C" alignas(16) uint8_t g_cineSampleVecPrev[32] = {};

// @ 0x82619AE0 (.data) — a 16-byte object in the image (zero); room for host pointer widths
extern "C" alignas(16) uint8_t g_cineSampleVec[32] = {};
