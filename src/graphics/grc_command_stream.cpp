#include "rage/grc_command_stream.hpp"

extern "C" void* grcDevice_AllocateCommandData(void* device, uint32_t words,
                                               uint32_t alignment); // @ 0x8235A088
extern "C" uint32_t KeGetCurrentProcessType(); // @ 0x82585E9C
extern const uint32_t __imp_VdGlobalDevice;    // @ 0x82000730
extern const uint32_t __imp_VdGlobalXamDevice; // @ 0x82000734
extern "C" void rage_EEC0(void* start, void* end); // @ 0x8235EEC0
extern "C" void rage_A4E0(void* device, uint32_t* count, uint32_t* source); // @ 0x8235A4E0
extern "C" void rage_A8C0(void* device, void* commands, uint32_t count,
                          uint32_t source, uint32_t flags, void* fixups); // @ 0x8235A8C0
extern "C" void rage_A780(void* device); // @ 0x8235A780
extern "C" uint32_t xe_GetCurrentThreadId(); // @ 0x82566B78
extern "C" void rage_AA78(void* device, uint32_t* handle); // @ 0x8235AA78
extern uint32_t g_grcThreadCommandTracking; // @ 0x8260663C
extern "C" int32_t rage_7BD0(void* device, uint32_t flush, uint32_t mask); // @ 0x82367BD0
extern "C" void rage_35A8(void* device, uint32_t flags); // @ 0x823535A8

namespace {
struct FixupList {
    uint32_t count;
    uint32_t* tail;
    uint32_t* cursor;
    uint32_t* end;
    void* device;
};

template<class T> T& field(void* device, uint32_t offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(device) + offset);
}

uint32_t gpuChainAddress(const void* pointer) {
    const uint32_t address = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(pointer));
    return (address & 0x1FFFFFFFu) + (((address >> 20) + 0x200u) & 0x1000u)
           - 0x40000000u;
}
} // namespace

// @ 0x82359B60 | size: 0x128
uint32_t* grc_9B60(void* object) {
    auto* list = static_cast<FixupList*>(object);
    if (list->tail != nullptr)
        *list->tail = gpuChainAddress(list->cursor);
    auto* block = static_cast<uint32_t*>(
        grcDevice_AllocateCommandData(list->device, 0x1080, 0x80));
    if (block == nullptr) {
        const uint32_t slot = KeGetCurrentProcessType() == 2
                            ? __imp_VdGlobalXamDevice : __imp_VdGlobalDevice;
        auto* device = *reinterpret_cast<uint8_t**>(static_cast<uintptr_t>(slot));
        block = *reinterpret_cast<uint32_t**>(device + 0x3D1C);
        list->count = 0;
    } else {
        block[0] = gpuChainAddress(block + 1);
        if (list->cursor != nullptr)
            *list->cursor = gpuChainAddress(block);
        const uint32_t address = gpuChainAddress(block);
        rage_EEC0(reinterpret_cast<void*>(static_cast<uintptr_t>(address)),
                  reinterpret_cast<void*>(static_cast<uintptr_t>(address + 0x1080)));
    }
    list->tail = block;
    list->cursor = block + 1;
    list->end = block + 0x41F;
    return block + 1;
}

// @ 0x8235A980 | size: 0xF8
extern "C" void* rage_A980(void* device) {
    if (field<uint32_t>(device, 0x34E0) == 0 &&
        (field<uint8_t>(device, 0x28C0) & 0x80) == 0) {
        uint32_t source, count;
        rage_A4E0(device, &count, &source);
        const uint32_t capturedSource = source;
        if (capturedSource != 0) {
            void* commands = grcDevice_AllocateCommandData(device, 4, 4);
            if (commands != nullptr)
                rage_A8C0(device, commands, count, capturedSource, 0,
                          static_cast<uint8_t*>(device) + 0x3504);
        }
    }
    rage_A780(device);
    if ((field<uint8_t>(device, 0x28C0) & 0x80) == 0 &&
        g_grcThreadCommandTracking != 0 &&
        (field<uint8_t>(device, 0x28C1) & 4) == 0) {
        uint32_t handle = field<uint32_t>(device, 0x289C) - 2;
        xe_GetCurrentThreadId();
        if (handle != 0)
            rage_AA78(device, &handle);
        field<uint8_t>(device, 0x28C1) |= 4;
    }
    return field<void*>(device, 0);
}

// @ 0x8235C660 | size: 0xC8
int32_t rage_C660(void* device) {
    field<uint8_t>(device, 0x28C0) &= 0xFD;
    rage_A980(device);
    auto* list = reinterpret_cast<FixupList*>(static_cast<uint8_t*>(device) + 0x3504);
    uint32_t* cursor = list->cursor;
    if (reinterpret_cast<uintptr_t>(cursor) + 4 > reinterpret_cast<uintptr_t>(list->end))
        cursor = grc_9B60(list);
    *cursor = 0x85000000u;
    list->cursor = cursor + 1;
    if ((field<uint8_t>(device, 0x28C0) & 0x10) == 0) {
        const uint32_t shift = field<uint32_t>(device, 0x2B38) & 63;
        const uint32_t mask = shift < 32 ? 0x01000000u << shift : 0;
        if (rage_7BD0(device, 1, mask) != 0) {
            rage_35A8(device, 0);
            return static_cast<int32_t>(0x8007000Eu);
        }
        if ((field<uint8_t>(device, 0x28C0) & 1) == 0)
            rage_35A8(device, 0);
    }
    return 0;
}
