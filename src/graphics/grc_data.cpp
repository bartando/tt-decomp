/**
 * grc_data.cpp — Graphics data the image defines
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


// @ 0x8202D110 (.rdata)
extern "C" const float g_grcRenderTargetDefaultLOD = 0.0f;

// @ 0x82035300 (.rdata)
extern "C" const char g_invalidTextureTypeMsg[61] = "Bad resource type %d in grcTextureFactoryXenon::PlaceTexture";

// @ 0x826063E8 (.data)
extern "C" void* g_grcRefCountedObjs[4] = {};

// @ 0x82606400 (.data)
extern "C" void* g_pGrcTextureFactoryString = nullptr;

// @ 0x82617E60 (.data)
extern "C" void* g_grcRenderObjects[2] = {};
