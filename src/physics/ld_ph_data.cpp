/**
 * ld_ph_data.cpp — physics data the image defines (link pass)
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Globals and constants that ph_physics.cpp, ph_update_object.cpp and
 * rage_core_utils.cpp reference but nothing defined. Each sits at the address
 * in its comment; constants take their value from the game image, pointers
 * start null (the image's values are PPC addresses), and vtables are
 * null-filled tables of the original's size. Names that the code uses for the
 * same address are aliases of one object.
 *
 * Some aliases point at objects defined in other files (ph_data.cpp,
 * globals.c, player_data.cpp) so the mutable state stays one object. On
 * Mach-O that becomes an indirect symbol (N_INDR) that ld resolves; an ELF
 * build would need those names defined next to their targets instead.
 */

#include <cstdint>
#include "link/tt_alias.h"

// @ 0x8202D108 (.rdata) — ph_ClampAndSin's upper clamp
extern "C" const float g_phClampMax = 1.0f;
TT_DATA_ALIAS("_ZN4rage26g_phBoundSurfaceOriginBiasE", "g_phClampMax");

// @ 0x8202D10C (.rdata) — the code calls it g_phTwo, but it is 0.5
extern "C" const float g_phTwo = 0.5f;
TT_DATA_ALIAS("_ZN4rage25g_phBoundSurfaceCellScaleE", "g_phTwo");

// @ 0x8202D110 (.rdata)
extern "C" const float g_phZeroFloat = 0.0f;
TT_DATA_ALIAS("g_phExtentScale", "g_phZeroFloat");
TT_DATA_ALIAS("g_phJoint1Dof_mass", "g_phZeroFloat");
TT_DATA_ALIAS("_ZN4rage28g_phBoundSurfaceInvCellScaleE", "g_phZeroFloat");

// @ 0x8202D13C (.rdata)
extern "C" const float g_phJoint1Dof_stiffness = 200.0f;

// @ 0x82079AD4 (.rdata) — -FLT_MAX
extern "C" const float g_phJoint1Dof_angleMin = -3.40282347e+38f;

// @ 0x82079AD8 (.rdata) — FLT_MAX
extern "C" const float g_phJoint1Dof_angleMax = 3.40282347e+38f;

// @ 0x82079B30 (.rdata) — pi; capsule volume = pi * r^2 * (4/3 r + h)
extern "C" const float g_capsuleVolK2 = 3.14159274f;
TT_DATA_ALIAS("g_phTaperedCapsuleVolK2", "g_capsuleVolK2");

// @ 0x82079BD0 (.rdata) — 4/3
extern "C" const float g_capsuleVolK1 = 1.33333337f;
TT_DATA_ALIAS("g_phTaperedCapsuleVolK1", "g_capsuleVolK1");

// @ 0x8207A04C (.rdata)
extern "C" const float g_phJoint1Dof_maxCorr = -1.0e+08f;

// @ 0x8207A050 (.rdata)
extern "C" const float g_phJoint1Dof_errTol = 1.0e+08f;

// @ 0x82005A58 (.rdata) — read with lhz
extern "C" uint16_t g_phDefaultStatusId = 10;

// @ 0x82006AF8 (.rdata) — [6][4][5] PPC code addresses (row 3 of each block
// is null), indexed (mode * 4 + base) * 5 + state; null in the port
extern "C" const uint32_t g_phStateTransitionTable[120] = {};

// @ 0x82027660 (.rdata) — scope-open marker written before the resolve pass
extern "C" const char* g_phResolveProfileTag = "{";

// @ 0x8202766C (.rdata)
extern "C" const char* g_phResolveProfileTagEnd = "}";

// @ 0x8203315C (.rdata) — rage::phJoint1Dof, 34 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_phJoint1DofVtable[34] = {};

// @ 0x8204FE9C (.rdata) — rage::phJoint, 34 slots
extern "C" void* const g_phJointVtable[34] = {};

// @ 0x8205872C (.rdata) — rage::phBoundOctree, 42 slots
extern "C" void* const g_phCollisionMgr_vtable[42] = {};

// @ 0x82059C3C (.rdata) — rage::phCollider, 69 slots
extern "C" void* const g_phBoundRelocVtable[69] = {};

// Not an address: operator new/delete pass this immediate (lis 0x648A; ori 0x18)
// to XMemAlloc/XMemFree as the allocation attributes.
extern "C" void* g_phAllocator = reinterpret_cast<void*>(uintptr_t{0x648A0018u});

namespace rage {
// @ 0x825C75A0 (.data)
extern const float g_phBoundSurfaceHalfBias = 16.0f;
}

// @ 0x825C8A50 (.data)
extern "C" const float g_phJoint1Dof_maxTorque = 10.0f;

// @ 0x825C9A40 (.data) — 2/5, solid-sphere inertia
extern "C" const float g_phSphereInertiaCoeff = 0.4f;

// @ 0x825D81B4 (.data) — 6 floats up to the next label
extern "C" float g_phTableB[6] = {1.0f, 0.0f, 0.5f, 0.0f, 0.0f, 0.0f};

// @ 0x826064E1 (.data) — zero in the image, set through a base register
extern "C" uint8_t g_phInstrumentEnabled = 0;


// @ 0x8271A32C (.data) — zero in the image, set at runtime
extern "C" uint32_t g_phRandomSeedPtr = 0;

// @ 0x8271A374 (.data) — zero in the image, set at runtime
extern "C" uint32_t g_phCollisionSolver = 0;

// @ 0x8271A7DC (.data) — 6 floats up to the next label, zero in the image
extern "C" float g_phTableA[6] = {};

// @ 0x8271B114 (.data) — 0xC4 bytes in the image, plus room for host pointer widths;
// runtime-initialised by 0x820C0038
extern "C" char g_mainThreadXtfStorage[256] = {};

// @ 0x8271B1D8 (.data) — runtime-initialised by 0x820C0038 (bit 0 = XTF block set up)
extern "C" uint32_t g_allocInitFlag = 0;
