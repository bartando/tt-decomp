#pragma once
#include "rage/ptr32.hpp"
struct plrPlayerMgr;
// Xbox game-memory singleton slot; four bytes on every host.
extern "C" rage::ptr32<plrPlayerMgr> g_plrPlayerMgr_state; // @ 0x82606430
static_assert(sizeof(g_plrPlayerMgr_state) == 4);
