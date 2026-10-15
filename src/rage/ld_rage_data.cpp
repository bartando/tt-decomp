/**
 * ld_rage_data.cpp — RAGE audio / graphics / shader data the image defines
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Globals and constants that code in rage/audio, rage_grm, rage_dat and
 * graphics references but nothing defined. Each sits at the address in its
 * comment; constants take their value from the game image, pointers start
 * null (the image's values are PPC addresses), and vtables are null-filled
 * tables of the original's size. Names that the code uses for the same
 * address are aliases of one object.
 */

#include <cstdint>
#include "link/tt_alias.h"

// An alias `off` bytes into `target` (same TU), for lifts that step from one
// global to its neighbour by pointer arithmetic.
#define LD_DATA_ALIAS_AT(alias, target, off)                    \
    __asm__(".globl " TT_ASM_SYMBOL(alias) "\n"                 \
            ".set " TT_ASM_SYMBOL(alias) ", " TT_ASM_SYMBOL(target) "+" #off)


// ── .rdata constants ────────────────────────────────────────────────────────

// @ 0x8202D108 (.rdata) — DrawDebugText's shadow X offset and the audVoiceSfx
// volume setters' offset (they send (volume - 1.0f) * 5000.0f)
extern "C" const float kDebugShadowOffsetX = 1.0f;
TT_DATA_ALIAS("_ZN4rage17g_audVolumeOffsetE", "kDebugShadowOffsetX");

// @ 0x8202D110 (.rdata) — DrawDebugText's alpha threshold and font scale;
// audVoiceStream::PlayByEntry's variance threshold
extern "C" const float kDebugFontScale = 0.0f;
TT_DATA_ALIAS("_ZN4rage14g_audZeroConstE", "kDebugFontScale");

// @ 0x8202D184 (.rdata)
extern "C" const float kDebugShadowOffsetY = 2.0f;

namespace rage {

// @ 0x8202D344 (.rdata)
extern const float g_audVolumeScaleFactor = 5000.0f;

// @ 0x8202D998 (.rdata) — not a table: three unrelated constants. PlayByEntry
// only reads [1] (0x8202D99C, log2(e)).
extern const float g_audRandomConstants[3] = {2.00501254e-08f, 1.44269502f, 330.0f};

// @ 0x820356B0 (.rdata) — audControlGroup slot 7
extern const char g_audControlGroupTypeName_short[] = "mix";

// @ 0x820356B4 (.rdata) — audControlGroup slot 6
extern const char g_audControlGroupTypeName[] = "tune\\audio";

// audControlGroup::LoadParameters (0x821629B8) field names
// @ 0x820356D0 (.rdata)
extern const char g_str_audControlGroup_field14[] = "MasterVolume";
// @ 0x820356E0 (.rdata)
extern const char g_str_audControlGroup_field1C[] = "Direct";
// @ 0x820356E8 (.rdata)
extern const char g_str_audControlGroup_field20[] = "Reverb";
// @ 0x820356F0 (.rdata)
extern const char g_str_audControlGroup_field24[] = "Effect";
// @ 0x820356F8 (.rdata)
extern const char g_str_audControlGroup_field2C[] = "MuteOnPause";
// @ 0x82035704 (.rdata)
extern const char g_str_audControlGroup_field2D[] = "PauseOnSilence";
// @ 0x82035714 (.rdata)
extern const char g_str_audControlGroup_field2E[] = "UseGlobalEffects";


// ── vtables ─────────────────────────────────────────────────────────────────

// @ 0x820276C4 (.rdata) — rage::datBase, 1 slot; audBankMgr's dtor ends on it
extern void* const g_audBankMgr_vtable[1] = {};

// @ 0x82027B34 (.rdata) — msgMsgSink, 2 slots
extern void* const g_msgMsgSink_vtable[2] = {};

// @ 0x82035768 (.rdata) — rage::audBankMgr, 1 slot
extern void* const g_audBankMgr_vtable_intermediate[1] = {};

// @ 0x82035A9C (.rdata) — rage::audVoice, 22 slots; audVoiceStream's dtor ends on it
extern void* const g_audVoiceStream_vtable[22] = {};

// @ 0x82035B5C (.rdata) — rage::audVoiceStream itself, 22 slots
extern void* const g_audVoiceStream_vtable_intermediate[22] = {};

// @ 0x82035D3C (.rdata) — 2 slots (slot 0 is the dtor 0x82166DC0)
extern void* const g_audSystem_vtable_A[2] = {};

// @ 0x82035D4C (.rdata) — 15 slots, the +4 subobject's
extern void* const g_audSystem_vtable_B[15] = {};


// ── .data ───────────────────────────────────────────────────────────────────

// @ 0x825CA91C (.data) — the lift reaches the active-voice list at 0x825CA920
// (vtable, prev, next) as +4; bytes 0..3 are the word before it, unused here
alignas(16) uint8_t g_audSfxVoiceFreeList[16] = {};

// @ 0x825CA938 (.data) — free stream-voice list (vtable, prev, next)
alignas(16) uint8_t g_audStreamVoiceFreeList[12] = {};

// @ 0x825E7888 (.data) — 4 bytes (next label 0x825E788C): the XAudio heap
// handle passed to the free at 0x824667D0, which ignores it
uint8_t g_audSceneList[4] = {};

// @ 0x825EBD2C (.data) — runtime-initialised
uint32_t* g_pAudCommandRingBuffer = nullptr;

// @ 0x825EE220 (.data) — runtime-initialised
uint32_t g_audCommandWriteIndex = 0u;

// @ 0x82618290 (.data) — 4 audControl3d of 176 bytes, runtime-initialised by 0x8257C678
alignas(16) uint8_t g_audControl3dArray[704] = {};

}  // namespace rage

// @ 0x825C8A50 (.data)
extern "C" float g_fastOrbitMul = 10.0f;

// @ 0x825C9030 (.data) — compared against 0x1A220197 by 0x8214EFE8; rewritten by 0x8214F400
extern "C" uint32_t g_grcFormatId = 0x2D200196u;

// @ 0x825C9A5C (.data) — three words; the variant lookups (0x820EF060,
// 0x820EFA08) read 0x825C9A60 as "the word before g_grmShaderFx_defaultVariant"
extern "C" alignas(4) int32_t g_grmShaderFx_forcedVariantId[3] = {-1, -1, -1};
// @ 0x825C9A64 (.data)
LD_DATA_ALIAS_AT("g_grmShaderFx_defaultVariant", "g_grmShaderFx_forcedVariantId", 8);

// @ 0x825EBA9C (.data) — runtime-initialised by 0x82153ED0
extern "C" void* g_pGrcDeviceAlt = nullptr;

// @ 0x825EBBD8 (.data) — runtime-initialised; the variant lookups read word 1
extern "C" alignas(16) uint32_t g_grmShaderFx_variantTable[2] = {};

// @ 0x825EBC40 (.data) — runtime-initialised
extern "C" void* g_pGrcTextureCache = nullptr;
