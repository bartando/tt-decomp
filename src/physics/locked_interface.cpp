#include "rage/locked_interface.hpp"

struct _RTL_CRITICAL_SECTION;
extern "C" void RtlEnterCriticalSection(_RTL_CRITICAL_SECTION* section); // @ 0x82585E0C
extern "C" void RtlLeaveCriticalSection(_RTL_CRITICAL_SECTION* section); // @ 0x82585DFC
extern "C" uint8_t g_phInterfaceLock[24]; // @ 0x825B2324

namespace {
struct RetainedInterfaceOps {
    virtual void ReservedSlot0() = 0;
    virtual uint32_t AddRef() = 0;
};
}

// @ 0x82460850
uint32_t phObject_AddRefLocked(void* object) {
    auto* lock = reinterpret_cast<_RTL_CRITICAL_SECTION*>(g_phInterfaceLock);
    RtlEnterCriticalSection(lock);
    const uint32_t result = static_cast<RetainedInterfaceOps*>(object)->AddRef();
    RtlLeaveCriticalSection(lock);
    return result;
}
