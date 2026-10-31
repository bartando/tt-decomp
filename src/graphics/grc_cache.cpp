#include "rage/grc_command_stream.hpp"
#if defined(__APPLE__) && !defined(__powerpc__)
#include <libkern/OSCacheControl.h>
#endif

namespace {
void flushGpuCacheLine(uintptr_t address) {
    void* line = reinterpret_cast<void*>(address);
#if defined(__powerpc__)
    __builtin_dcbf(line);
#elif defined(__APPLE__)
    sys_dcache_flush(line, 128);
#elif defined(__x86_64__) || defined(__i386__)
    __builtin_ia32_clflush(line);
#else
#error A data-cache flush implementation is required for this architecture
#endif
}
} // namespace

// @ 0x8235EEC0 | size: 0xA0
extern "C" void rage_EEC0(void* start, void* end) {
    const uintptr_t begin = reinterpret_cast<uintptr_t>(start);
    // This Xenon mapping is already coherent; it needs neither flush nor sync.
    constexpr uint32_t coherentWindowBase = 0x7F100000u;
    constexpr uint32_t coherentWindowSpan = 0x07EFFFFFu;
    if (begin <= UINT32_MAX && static_cast<uint32_t>(begin - coherentWindowBase) <= coherentWindowSpan)
        return;
    uintptr_t cursor = begin & ~uintptr_t(127);
    const uintptr_t limit = (reinterpret_cast<uintptr_t>(end) + 127) & ~uintptr_t(127);
    uint32_t lines = static_cast<uint32_t>((limit - cursor) / 128);
    while (lines-- != 0) {
        flushGpuCacheLine(cursor);
        cursor += 128;
    }
#if defined(__powerpc__)
    __builtin_ppc_sync();
#else
    __sync_synchronize();
#endif
}
