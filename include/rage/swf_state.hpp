#pragma once
#include <cstdint>
namespace rage {
struct swfGlyphRenderState { float matrix[6]; void* texture; };
struct swfLineRenderState { float uvMatrix[6]; float matrix[6]; };
extern swfGlyphRenderState g_swfGlyphRenderState; // @ 0x82606120
extern swfLineRenderState g_swfLineRenderState; // @ 0x8260613C
extern void* g_swfCurrentFile; // @ 0x82602838
extern const float g_swfTwipScale; // @ 0x820290F0
extern const float g_swfTwipsToPixels; // Same constant.
}
extern "C" {
extern void (*g_swfBindFontTexture)(void*); // @ 0x82602820
extern uint32_t g_swfNodePool; // @ 0x82604C5C — guest VM pool identity
extern uint32_t g_swfMemberNodePool; // @ 0x82604C54
extern uint32_t g_swfPriorityMemberHashes[13]; // @ 0x82604CE8
extern uint8_t g_swfPriorityMemberHashesReady; // @ 0x826066C8
extern const char* const g_swfPriorityMemberNames[13]; // @ 0x825C2D30
}
