#include "rage/swf_state.hpp"
#include "link/tt_alias.h"
// Each complete mutable image span is zero, including the glyph texture slot.
namespace rage {
swfGlyphRenderState g_swfGlyphRenderState = {}; // @ 0x82606120, 28 guest bytes
swfLineRenderState g_swfLineRenderState = {}; // @ 0x8260613C, 48 bytes
void* g_swfCurrentFile = nullptr; // @ 0x82602838
extern const float g_swfTwipScale = 0x1.99999ap-5f; // @ 0x820290F0
}
TT_DATA_ALIAS("_ZN4rage18g_swfTwipsToPixelsE", "_ZN4rage14g_swfTwipScaleE");
extern "C" {
void (*g_swfBindFontTexture)(void*) = nullptr; // @ 0x82602820
void* g_swfNodePool = nullptr; // @ 0x82604C5C
void* g_swfMemberNodePool = nullptr; // @ 0x82604C54
uint32_t g_swfPriorityMemberHashes[13] = {}; // @ 0x82604CE8
uint8_t g_swfPriorityMemberHashesReady = 0; // @ 0x826066C8
// Relocated native string pointers, in the exact 13-entry image order.
extern const char* const g_swfPriorityMemberNames[13] = {"_global", "i", "j", "k", "x", "y", "z", "f", "Array", "0", "1", "2", "3"}; // @ 0x825C2D30
}
