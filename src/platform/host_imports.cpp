#include "platform/video_imports.h"
#include <cstdint>

namespace {
void* titleVideoDevice = nullptr;
void* systemVideoDevice = nullptr;
constexpr uint32_t HostXamNotSupported = 50;
}
extern "C" {
void** __imp_VdGlobalDevice = &titleVideoDevice;
void** __imp_VdGlobalXamDevice = &systemVideoDevice;
uint32_t KeGetCurrentProcessType() { return 1; } // Title/user process, not XAM.
uint32_t XamEnumerate(uint32_t, void*, uint32_t, uint32_t* itemCount, void*) {
    if (itemCount) *itemCount = 0;
    return HostXamNotSupported; // No Xbox enumerator/service namespace on the host.
}
}
