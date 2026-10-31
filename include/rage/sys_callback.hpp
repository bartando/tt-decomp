#pragma once
#include <cstdint>

// Three pointer words and a 32-bit mode; the Xenon image occupies 16 bytes.
struct SystemCallback {
    void* target;
    void (*function)();
    void* storedArgument;
    uint32_t kind;
};

// @ 0x8225FFF8 — dispatch a datCallback, with an optional runtime argument.
extern "C" void sysCallback_Invoke(void* callback, void* argument);
