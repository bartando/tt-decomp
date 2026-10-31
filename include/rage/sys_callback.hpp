#pragma once
#include <cstdint>

// Four pointer-sized words in the host port; four 32-bit words in the image.
// target is a direct function address, mode selects the argument shape.
struct SysCallback {
    void* self;
    uintptr_t target;
    uintptr_t context;
    uintptr_t mode;
};

extern "C" void sysCallback_Invoke(void* callback, uintptr_t argument); // @ 0x8225FFF8
