/**
 * creature_data.cpp — Creature data the image defines
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
extern "C" const float g_twoPi = 6.28318548f;

// @ 0x825C8078 (.data)
extern "C" float g_blendCurveOffset = 0.00999999978f;
TT_DATA_ALIAS("g_kCourtHeightOffset", "g_blendCurveOffset");

// @ 0x825C9D64 (.data) — mover stationary speed/timer threshold
extern "C" float lbl_825C9D64 = 25.0f;

// @ 0x825C9F3C (.data)
extern "C" alignas(16) uint32_t lbl_825C9F3C[5] = {0x8202783Cu, 0x0u, 0x0u, 0x0u, 0x0u};

// @ 0x82606325 (.data)
extern "C" uint8_t lbl_82606325 = 0x0u;

// @ 0x82606326 (.data) — mover velocity adjustment enabled
extern "C" uint8_t lbl_82606326 = 0;

// @ 0x82606750 (.data)
extern "C" alignas(16) float lbl_82606750[4] = {0.0f, 0.0f, 0.0f, 0.0f};
/* pong_player.cpp and anim_blender_init.cpp/cloth.cpp name the same vector */
TT_DATA_ALIAS("g_kVecConst_606750", "lbl_82606750");
TT_DATA_ALIAS("g_playerMirrorPlane", "lbl_82606750");
TT_DATA_ALIAS("g_zeroVec4", "lbl_82606750");

// @ 0x825C9D60 (.data) — duration before clearing the movement latch
extern "C" float g_moverStartDelay = 1.75f;

// @ 0x820290F0 (.rdata) — zero-input delay before restoring the latch
extern "C" const float g_moverStopDelay = 0.05000000074505806f;
