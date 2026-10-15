/**
 * anim_data.cpp — RAGE animation data the image defines
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


// @ 0x820283B8 (.rdata) — 3 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_pcrAnimObserver_vtable[3] = {};

// @ 0x820283C4 (.rdata) — 2 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_pcrAnimObserverHash_vtable[2] = {};

// @ 0x8203A928 (.rdata) — 13 slots of PPC code addresses in the image, null in the port
extern "C" void* const g_xmlTree_vtable[13] = {};
