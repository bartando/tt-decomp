#include "rage/fi_stream_internal.hpp"
#include "xam/kernel.h"

extern "C" {
// @ 0x8240E6D0 — release formatter is a single blr; the open logger supplies a
// channel before the format string, unlike the diagnostic call sites.
void nop_8240E6D0(uint32_t channel, const char* format, const char* path,
                    uint32_t flags, const char* status);
// @ 0x8240E6D0
void rage_DebugLog(const char* format, ...);
// @ 0x8242F7D0
int xe_atexit(void (*callback)());
}

// @ 0x821880D0
extern "C" void fiStreamLock_Acquire(rage::fiStreamLockScope* scope) {
    if (scope->locked == 0)
        RtlEnterCriticalSection(scope->section.get());
    scope->locked = 1;
}

// @ 0x82188130
extern "C" void fiStreamLock_Release(rage::fiStreamLockScope* scope) {
    if (scope->locked == 1)
        RtlLeaveCriticalSection(scope->section.get());
    scope->locked = 0;
}

// @ 0x825841D8
extern "C" void fiStreamBuf_AtExit() {}

// @ 0x822E3378
extern "C" void* fiStreamBuf_Attach(const char*, uint32_t handle, rage::fiStreamDevice* device) {
    auto* section = reinterpret_cast<RTL_CRITICAL_SECTION*>(g_fiStreamLock);
    if ((g_fiStreamLockInit & 1) == 0) {
        g_fiStreamLockInit |= 1;
        RtlInitializeCriticalSection(section);
        xe_atexit(fiStreamBuf_AtExit);
    }
    rage::fiStreamLockScope scope;
    scope.locked = 0;
    scope.section = section;
    fiStreamLock_Acquire(&scope);
    int32_t index = 0;
    while (index < 12 && g_fiStreamPool[index].device) ++index;
    if (index == 12) {
        rage_DebugLog("Out of file handles.");
        if (scope.locked == 1)
            RtlLeaveCriticalSection(scope.section.get());
        return nullptr;
    }
    auto* stream = &g_fiStreamPool[index];
    const int32_t highWater = g_fiStreamHighWater;
    stream->handle = handle;
    stream->capacity = 4096;
    stream->position = 0;
    stream->cursor = 0;
    stream->end = 0;
    stream->buffer = g_fiStreamBuffers[index];
    stream->device = device;
    if (index > highWater) g_fiStreamHighWater = index;
    if (scope.locked != 0) fiStreamLock_Release(&scope);
    return stream;
}

// @ 0x822E34C0
extern "C" void* fiStreamBuf_OpenFailed(const char* path) {
    if (g_fiMissingFileOptionValue)
        rage_DebugLog("Missing filename: %s", path);
    return nullptr;
}

// @ 0x822E3518
extern "C" void* fiStream_Open(const char* path, int32_t flags) {
    auto* device = static_cast<rage::fiStreamDevice*>(fiDevice_GetDevice(path, flags));
    if (!device) return fiStreamBuf_OpenFailed(path);
    const int32_t handle = device->Open(path, flags);
    nop_8240E6D0(g_fiOpenLogChannel, "fiStream::Open(%s,%d) %s", path,
                   static_cast<uint8_t>(flags), handle != -1 ? "ok" : "failed");
    if (handle != -1 && g_fiOpenCallback) {
        if (static_cast<uint8_t>(g_fiOpenCallback.get()(path, flags)) == 0) {
            device->Close(handle);
            return fiStreamBuf_OpenFailed(path);
        }
    }
    if (handle == -1) return fiStreamBuf_OpenFailed(path);
    return fiStreamBuf_Attach(path, handle, device);
}
