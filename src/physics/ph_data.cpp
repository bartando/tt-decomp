/**
 * ph_data.cpp — Physics data the image defines
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


// @ 0x8202C02C (.rdata)
extern "C" const float g_phTwoPi = 6.28318548f;

// @ 0x8202D110 (.rdata)
extern "C" const float g_physZeroF = 0.0f;

// @ 0x8202D114 (.rdata)
extern "C" const float g_physOneF = 300.0f;

// @ 0x82050078 (.rdata) — 2 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_phJointChainVtable[2] = {};

// @ 0x82058494 (.rdata) — 43 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_phBoundGeometryVtable[43] = {};

// @ 0x82079B30 (.rdata)
extern "C" const float g_capsuleRadius = 3.14159274f;

// @ 0x82079C30 (.rdata)
extern "C" const float g_phSphereVolumeCoeff = 4.18879032f;

// @ 0x82079D18 (.rdata)
extern "C" const float g_phNegThreshold = -0.0f;

// @ 0x8207A008 (.rdata)
extern "C" const float g_dampingScale = 0.707000017f;

// @ 0x8207A0F4 (.rdata)
extern "C" const float g_springScale = 17.0f;

// @ 0x825C48E8 (.data)
extern "C" uint32_t g_phCollisionFlags = 0xFFFFFFFFu;

// @ 0x825C8080 (.data)
extern "C" float g_phCapsuleShapeK = 0.25f;

// @ 0x825E7890 (.data)
extern "C" uint32_t g_mmioStoredValue = 0x0u;

// @ 0x826063C4 (.data)
extern "C" void* g_animState = nullptr;

// @ 0x826064E0 (.data)
extern "C" uint8_t g_physicsDisabled = 0x0u;

// @ 0x826066E4 (.data)
extern "C" void* g_phMaterialAllocator = nullptr;
