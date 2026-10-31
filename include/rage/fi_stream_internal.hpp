#pragma once
#include "rage/fi_stream.hpp"
struct _RTL_CRITICAL_SECTION;
namespace rage {
struct fiStreamLockScope {
    uint8_t locked;
    uint8_t padding[3];
    ptr32<_RTL_CRITICAL_SECTION> section;
};
using fiOpenCallback = uint32_t(const char*, int32_t);
}
extern "C" {
extern uint8_t g_fiStreamLock[32]; // @ 0x8271B210
extern uint32_t g_fiStreamLockInit; // @ 0x8271B230
extern rage::fiStreamBuf g_fiStreamPool[12]; // @ 0x825F5D00
extern uint8_t g_fiStreamBuffers[12][4096]; // @ 0x825F5E50
extern int32_t g_fiStreamHighWater; // @ 0x825C4818
extern rage::ptr32<rage::fiOpenCallback> g_fiOpenCallback; // @ 0x825F5CF0
extern uint32_t g_fiOpenLogChannel; // @ 0x825F5CF8
extern rage::ptr32<void> g_fiMissingFileOptionValue; // @ 0x825D06B4
void fiStreamLock_Acquire(rage::fiStreamLockScope* scope); // @ 0x821880D0
void fiStreamLock_Release(rage::fiStreamLockScope* scope); // @ 0x82188130
void fiStreamBuf_AtExit(); // @ 0x825841D8 — original release-build callback is blr.
void* fiStreamBuf_Attach(const char* path, uint32_t handle, rage::fiStreamDevice* device); // @ 0x822E3378
void* fiStreamBuf_OpenFailed(const char* path); // @ 0x822E34C0
}
