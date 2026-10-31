#include "rage/swf_state.hpp"
#include "rage/localized_font.hpp"
#include "link/tt_alias.h"
// Mutable SWF state and font shutdown storage reproduced from the image.
namespace rage {
swfGlyphRenderState g_swfGlyphRenderState = {}; // @ 0x82606120, 28 guest bytes
swfLineRenderState g_swfLineRenderState = {}; // @ 0x8260613C, 48 bytes
void* g_swfCurrentFile = nullptr; // @ 0x82602838
extern const float g_swfTwipScale = 0x1.99999ap-5f; // @ 0x820290F0
}
TT_DATA_ALIAS("_ZN4rage18g_swfTwipsToPixelsE", "_ZN4rage14g_swfTwipScaleE");
extern "C" {
rage::ptr32<LocalizedFont> g_localizedFontHead; // @ 0x826066E0
LocalizedFontShutdownRecord g_localizedFontShutdownRecords[32]{}; // @ 0x8261A1D0
LocalizedFontShutdownRegistry g_localizedFontShutdownRegistry{ // @ 0x825CB9A0
    g_localizedFontShutdownRecords, 0, 32
};
extern const char g_localizedFontReleaseError[] = "txtFreeFontTex() - font not found in font list"; // @ 0x8207580C
extern const char g_localizedFallbackFont[] = "arial12"; // @ 0x82075804
char g_swfInternedText[8192] = {}; // @ 0x82602848 — 128 slots of 64 bytes
void (*g_swfBindFontTexture)(void*) = nullptr; // @ 0x82602820
void* g_swfNodePool = nullptr; // @ 0x82604C5C
void* g_swfMemberNodePool = nullptr; // @ 0x82604C54
uint32_t g_swfPriorityMemberHashes[13] = {}; // @ 0x82604CE8
uint8_t g_swfPriorityMemberHashesReady = 0; // @ 0x826066C8
// Relocated native string pointers, in the exact 13-entry image order.
extern const char* const g_swfPriorityMemberNames[13] = {"_global", "i", "j", "k", "x", "y", "z", "f", "Array", "0", "1", "2", "3"}; // @ 0x825C2D30
}
