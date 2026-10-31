#include "rage/fi_stream_internal.hpp"
extern "C" {
// @ 0x825D06A0 — long-filename replacement option, absent at boot.
rage::ptr32<void> g_fiLongNameOptionValue;
// @ 0x8271B210
alignas(4) uint8_t g_fiStreamLock[32] = {};
// @ 0x8271B230
uint32_t g_fiStreamLockInit = 0;
// @ 0x825F5D00
rage::fiStreamBuf g_fiStreamPool[12];
// @ 0x825F5E50
uint8_t g_fiStreamBuffers[12][4096] = {};
// @ 0x825C4818
int32_t g_fiStreamHighWater = -1;
// @ 0x825F5CF0
rage::ptr32<rage::fiOpenCallback> g_fiOpenCallback;
// @ 0x825F5CF8
uint32_t g_fiOpenLogChannel = 0;
// @ 0x825D06B4
rage::ptr32<void> g_fiMissingFileOptionValue;
// @ 0x826065EA
uint8_t g_fiFallbackReadOnly = 0;
}
