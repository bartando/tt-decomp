#include "platform/audio.hpp"
#include "link/tt_alias.h"
#include "rage/ptr32.hpp"
// @ 0x825E7870 — all 16 image bytes are zero; both names share this lock.
XAudioLock g_xaudioSourceLock = {};
TT_DATA_ALIAS("_ZN4rage14g_audMixerLockE", "g_xaudioSourceLock");
extern const float g_xmaFadeScale = 0x1p-1f; // @ 0x82005A5C
namespace rage {
struct audInstance;
// Full image spans checked: 64-byte listener and 16/240 null pointer slots.
alignas(16) uint8_t g_audListener[64] = {}; // @ 0x825EE258
ptr32<audInstance> g_audInstancePool2000[16] = {}; // @ 0x825EE658
ptr32<audInstance> g_audInstancePool4000[240] = {}; // @ 0x825EE298
extern const char g_audDistanceParameter[] = "Distance"; // @ 0x8203b4e8
extern const char g_audPitchParameter[] = "Pitch"; // @ 0x8203B4E0
extern const char g_audInvalidXactCommand[] = "AgeSnd: xactSound: Not a xactSound command SfxNum = %d, command = %d\n"; // @ 0x8203b2b0
}
