/**
 * char_view_data.cpp — Character viewer data the image defines
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


// @ 0x825C5938 (.data) — a 16-byte object in the image: its values with pointers nulled, plus room for host pointer widths
extern "C" alignas(16) float g_charViewCS_scale[8] = {-1.0f, 2.80259693e-45f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
TT_DATA_ALIAS("g_fDrillDefaultTime", "g_charViewCS_scale");
TT_DATA_ALIAS("g_kFloatConst_5C5938", "g_charViewCS_scale");
TT_DATA_ALIAS("g_kPositiveSideSign", "g_charViewCS_scale");
TT_DATA_ALIAS("lbl_825C5938", "g_charViewCS_scale");
TT_DATA_ALIAS("g_kInputScale", "g_charViewCS_scale");
TT_DATA_ALIAS("g_msgSinkInitFloat", "g_charViewCS_scale");
TT_DATA_ALIAS("g_defaultTimeout", "g_charViewCS_scale");
TT_DATA_ALIAS("g_fDefaultTimer", "g_charViewCS_scale");
