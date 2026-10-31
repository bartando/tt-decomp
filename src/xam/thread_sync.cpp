#include "xam/thread_sync.h"
#include <cstdint>

extern "C" void* g_sda_base; // @ 0x82600000 — host representation of r13
extern "C" uint32_t RtlNtStatusToDosError(int32_t status); // @ 0x82585E5C
extern "C" int32_t NtWaitForSingleObjectEx(void* handle, uint32_t mode,
                                          uint32_t alertable, const int64_t* timeout); // @ 0x82585EFC
extern "C" int32_t NtReleaseSemaphore(void* handle, int32_t count, int32_t* previousCount); // @ 0x8258666C

// @ 0x8242C390 | size: 0x20
extern "C" int64_t* sysThread_MillisecondsTimeout(int64_t* storage, uint32_t milliseconds) {
    if (milliseconds == UINT32_MAX) return nullptr;
    *storage = -static_cast<int64_t>(milliseconds) * 10000;
    return storage;
}

// @ 0x8242C330 | size: 0x34
extern "C" uint32_t sysThread_SetErrorFromStatus(int32_t status) {
    uint32_t error = RtlNtStatusToDosError(status);
    auto* sda = static_cast<uint8_t*>(g_sda_base);
    if (*reinterpret_cast<uint32_t*>(sda + 0x150) == 0) {
        auto* thread = *reinterpret_cast<uint8_t**>(sda + 0x100);
        *reinterpret_cast<uint32_t*>(thread + 0x160) = error;
    }
    return error;
}

// @ 0x8242BF10 | size: 0x4 — formerly misnamed game_CrtFatalExit_thunk.
extern "C" uint32_t sysThread_SetErrorFromStatusThunk(int32_t status) {
    return sysThread_SetErrorFromStatus(status);
}

// @ 0x8242F5D0 | size: 0x64
extern "C" uint32_t sysThread_WaitTimeoutEx(void* handle, uint32_t milliseconds, uint32_t alertable) {
    int64_t storage;
    int64_t* timeout = sysThread_MillisecondsTimeout(&storage, milliseconds);
    for (;;) {
        int32_t status = NtWaitForSingleObjectEx(handle, 1, alertable & 0xFFu, timeout);
        if (status < 0) {
            sysThread_SetErrorFromStatus(status);
            return UINT32_MAX;
        }
        // Retail tests the full original flag here, rather than its low byte.
        if (alertable == 0 || status != 0x101) return static_cast<uint32_t>(status);
    }
}

// @ 0x8242C3B8 | size: 0x8
extern "C" uint32_t sysThread_WaitTimeout(void* handle, int milliseconds) {
    return sysThread_WaitTimeoutEx(handle, static_cast<uint32_t>(milliseconds), 0);
}

// @ 0x82566DC0 | size: 0x38
extern "C" uint32_t sysThread_ReleaseSemaphore(void* handle, int32_t count, int32_t* previousCount) {
    int32_t status = NtReleaseSemaphore(handle, count, previousCount);
    if (status < 0) {
        sysThread_SetErrorFromStatusThunk(status);
        return 0;
    }
    return 1;
}
