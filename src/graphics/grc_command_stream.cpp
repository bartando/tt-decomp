#include "rage/grc_command_stream.hpp"
#include <cstring>

extern "C" void* grcDevice_AllocateCommandData(void* device, uint32_t words,
                                               uint32_t alignment); // @ 0x8235A088
extern "C" uint32_t KeGetCurrentProcessType(); // @ 0x82585E9C
extern const uint32_t __imp_VdGlobalDevice;    // @ 0x82000730
extern const uint32_t __imp_VdGlobalXamDevice; // @ 0x82000734
extern "C" uint32_t xe_GetCurrentThreadId(); // @ 0x82566B78
extern uint32_t g_grcThreadCommandTracking; // @ 0x8260663C
extern "C" uint32_t KfAcquireSpinLock(void* lock); // @ 0x825862CC
extern "C" void KfReleaseSpinLock(void* lock, uint32_t irql); // @ 0x825862EC
extern "C" void* rage_9C88(void* list, void* commands, uint32_t wordCount,
                           uint32_t gpuAddress); // @ 0x82359C88
extern "C" void phInst_A340_p42(void* device, const uint32_t* packet, uint32_t flags); // @ 0x8235A340
extern "C" void* phInst_A6A8_p42(void* device, void* cursor); // @ 0x8235A6A8
extern "C" void grc_5E08(void* device, const void* rect); // @ 0x82355E08
extern "C" void rage_6858(void* device, uint32_t index, const float* plane); // @ 0x82356858
extern "C" void rage_7A20(uint32_t context); // @ 0x82367A20
extern "C" uint32_t* phInst_AB60_v12(void* device, uint32_t* cursor, uint32_t mask,
                                    void (*callback)(uint32_t), uint32_t fixups); // @ 0x8235AB60

namespace {
struct FixupList {
    uint32_t* head;
    uint32_t* tail;
    uint32_t* cursor;
    uint32_t* end;
    void* device;
};

template<class T> T& field(void* device, uint32_t offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(device) + offset);
}

uint32_t gpuPhysicalAddress(uint32_t address) {
    return (address & 0x1FFFFFFFu) + (((address >> 20) + 0x200u) & 0x1000u);
}

uint32_t gpuChainAddress(const void* pointer) {
    return gpuPhysicalAddress(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(pointer)))
           - 0x40000000u;
}
} // namespace

// @ 0x8235A4E0 | size: 0x1C4
extern "C" void rage_A4E0(void* device, uint32_t* gpuAddress, uint32_t* wordCount) {
    constexpr uint64_t emptyRange = UINT64_C(0xFFFFFFFF);
    const bool pending = __atomic_load_n(&field<uint64_t>(device, 0x2C98), __ATOMIC_RELAXED) != emptyRange;
    const bool ringWrapped = (field<uint8_t>(device, 0x28C2) & 0x10) != 0;
    const uint32_t words = 11u * (static_cast<uint32_t>(pending) + static_cast<uint32_t>(ringWrapped));
    if (words == 0) {
        *wordCount = 0;
        return;
    }
    auto* packet = static_cast<uint32_t*>(grcDevice_AllocateCommandData(device, words, 32));
    if (packet == nullptr) {
        *wordCount = 0;
        return;
    }
    uint32_t* output = packet;
    const auto emitRange = [&output](uint32_t flags, uint32_t first, uint32_t last) {
        output[0] = 0xA31;
        output[1] = flags;
        output[2] = 0x10A2F;
        output[3] = last - first;
        output[4] = first;
        output[5] = 0xC0043C00;
        output[6] = 3;
        output[7] = 0xA31;
        output[8] = 0;
        output[9] = 0x80000000;
        output[10] = 8;
        output += 11;
    };
    if (pending) {
        const uint64_t range = __atomic_exchange_n(&field<uint64_t>(device, 0x2C98), emptyRange, __ATOMIC_SEQ_CST);
        const uint32_t first = static_cast<uint32_t>(range) & 0xFFFFF000u;
        const uint32_t last = (static_cast<uint32_t>(range >> 32) + 4095) & 0xFFFFF000u;
        emitRange(0x03000000, first, last);
    }
    if (ringWrapped) {
        const uint32_t first = gpuPhysicalAddress(field<uint32_t>(device, 0x36B4)) & 0xFFFFF000u;
        const uint32_t last = (gpuPhysicalAddress(field<uint32_t>(device, 0x36B8)) + 4095) & 0xFFFFF000u;
        emitRange(0x01000000, first, last);
    }
    *wordCount = words;
    *gpuAddress = gpuPhysicalAddress(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(packet)));
}

// @ 0x8235A8C0 | size: 0xBC
extern "C" void* rage_A8C0(void* device, void* commands, uint32_t gpuAddress,
                           uint32_t wordCount, uint32_t flags, void* fixups) {
    if (field<uint32_t>(device, 0x28FC) != 0) {
        void* lock = static_cast<uint8_t*>(device) + 0x2900;
        const uint32_t irql = KfAcquireSpinLock(lock);
        bool queued = false;
        if (field<uint32_t>(device, 0x28FC) != 0) {
            commands = rage_9C88(fixups, commands, wordCount, gpuAddress);
            field<uint32_t>(device, 0x28FC) += flags;
            queued = true;
        }
        KfReleaseSpinLock(lock, irql);
        if (queued)
            return commands;
    }
    uint32_t packet[2] = {wordCount, gpuAddress};
    field<uint32_t>(device, 0x28FC) += flags;
    phInst_A340_p42(device, packet, 1);
    return commands;
}

// @ 0x8235A780 | size: 0x13C
extern "C" void rage_A780(void* device) {
    auto* cursor = field<uint32_t*>(device, 0) + 1;
    auto* start = field<uint32_t*>(device, 0x36CC);
    if ((field<uint8_t>(device, 0x28C1) & 0x80) == 0 &&
        (field<uint8_t>(device, 0x28C0) & 0x80) == 0) {
        if (field<uint32_t>(device, 0x34E0) != 0) {
            const uint32_t words = static_cast<uint32_t>(
                static_cast<int32_t>(reinterpret_cast<uintptr_t>(cursor) - reinterpret_cast<uintptr_t>(start)) >> 2);
            if (words != 0) {
                auto* list = reinterpret_cast<FixupList*>(static_cast<uint8_t*>(device) + 0x3504);
                uint32_t* entry = list->cursor;
                if (reinterpret_cast<uintptr_t>(entry) + 8 > reinterpret_cast<uintptr_t>(list->end))
                    entry = grc_9B60(list);
                entry[0] = 0x81000000u | words;
                entry[1] = gpuPhysicalAddress(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(start)));
                list->cursor = entry + 2;
            }
        } else {
            auto* end = static_cast<uint32_t*>(phInst_A6A8_p42(device, cursor));
            const uint32_t words = static_cast<uint32_t>(
                static_cast<int32_t>(reinterpret_cast<uintptr_t>(end) - reinterpret_cast<uintptr_t>(start)) >> 2);
            cursor = static_cast<uint32_t*>(rage_A8C0(device, end,
                gpuPhysicalAddress(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(start))), words, 0,
                static_cast<uint8_t*>(device) + 0x3504));
        }
    }
    const uintptr_t aligned = (reinterpret_cast<uintptr_t>(cursor) + 31) & ~uintptr_t(31);
    if (aligned > reinterpret_cast<uintptr_t>(field<uint32_t*>(device, 8))) {
        field<uint32_t*>(device, 0) = cursor - 1;
        rage_A150(device, 0);
    } else {
        field<uint32_t*>(device, 0x36CC) = reinterpret_cast<uint32_t*>(aligned);
        field<uint32_t*>(device, 0) = reinterpret_cast<uint32_t*>(aligned) - 1;
        if (field<void*>(device, 0x4FE0) != nullptr && field<uint32_t>(device, 0x36C0) != 0)
            field<uint32_t>(device, 0x36C0) = (field<uint32_t>(device, 0x36C0) + 4095) & 0xFFFFF000u;
    }
}

// @ 0x823535A8 | size: 0x140
extern "C" void rage_35A8(void* device, uint32_t flags) {
    uint32_t* cursor = field<uint32_t*>(device, 0);
    if (reinterpret_cast<uintptr_t>(cursor) > reinterpret_cast<uintptr_t>(field<uint32_t*>(device, 8)))
        cursor = static_cast<uint32_t*>(rage_A980(device));
    if ((flags & 1) == 0) {
        *++cursor = 0xC0015000;
        const uint32_t mask = field<uint32_t>(device, 0x32A0);
        *++cursor = mask != 0 ? mask : 0xFFFFFFFFu;
        *++cursor = 0;
        *++cursor = 0xC0015100;
        *++cursor = 0xFFFFFFFFu;
        *++cursor = 0xFFFFFFFFu;
    }
    field<uint32_t*>(device, 0) = cursor;
    grc_5E08(device, static_cast<uint8_t*>(device) + 0x3220);
    for (uint32_t index = 0; index < 6; ++index) {
        float plane[4];
        std::memcpy(plane, static_cast<uint8_t*>(device) + 0x3230 + index * 16, sizeof(plane));
        rage_6858(device, index, plane);
    }
    if ((flags & 2) == 0) {
        cursor = field<uint32_t*>(device, 0);
        if (reinterpret_cast<uintptr_t>(cursor) > reinterpret_cast<uintptr_t>(field<uint32_t*>(device, 8)))
            cursor = static_cast<uint32_t*>(rage_A980(device));
        *++cursor = 0x5C8;
        *++cursor = 0x20000;
        *++cursor = 0xF01;
        *++cursor = field<uint32_t>(device, 0x28A0);
        field<uint32_t*>(device, 0) = cursor;
    }
    for (uint32_t offset = 0x10; offset <= 0x30; offset += 8)
        field<uint64_t>(device, offset) = UINT64_MAX;
}

// @ 0x82367BD0 | size: 0x204
extern "C" int32_t rage_7BD0(void* device, uint32_t flush, uint32_t mask) {
    uint32_t gpuAddress = 0, wordCount = 0;
    if ((field<uint8_t>(device, 0x28C1) & 0x80) == 0)
        rage_A4E0(device, &gpuAddress, &wordCount);
    auto* commands = static_cast<uint32_t*>(grcDevice_AllocateCommandData(device, 0x64, 32));
    uint32_t* end;
    if (commands != nullptr) {
        const uint32_t fixups = gpuChainAddress(field<void*>(device, 0x3504));
        end = phInst_AB60_v12(device, commands - 1, mask | 1, rage_7A20, fixups) + 1;
    } else {
        end = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(gpuAddress));
    }
    void* continuation = grcDevice_AllocateCommandData(device, 0x20, 4);
    if (continuation == nullptr)
        continuation = reinterpret_cast<void*>(static_cast<uintptr_t>(gpuAddress));
    const uint8_t mode = field<uint8_t>(device, 0x28C1);
    field<uint32_t>(device, 0x34E0) = 0;
    field<uint32_t>(device, 0x34E4) = 0;
    if ((mode & 0x80) != 0) {
        field<uint32_t>(device, 0) = field<uint32_t>(device, 0x352C);
        field<uint32_t>(device, 4) = field<uint32_t>(device, 0x3530);
        field<uint32_t>(device, 0x36CC) = field<uint32_t>(device, 0x3534);
        field<uint32_t>(device, 0x36C8) = field<uint32_t>(device, 0x3538);
        field<uint32_t>(device, 0x36C0) = field<uint32_t>(device, 0x353C);
        field<uint32_t>(device, 0x36C4) = field<uint32_t>(device, 0x3540);
        field<uint8_t>(device, 0x28C1) = mode & 0x7F;
        field<uint32_t>(device, 8) = field<uint32_t>(device, 0x3530) - 0xA0;
        return 1;
    }
    const uint32_t lists[2] = {0x3504, 0x34F0};
    for (uint32_t offset : lists) {
        auto* list = reinterpret_cast<FixupList*>(static_cast<uint8_t*>(device) + offset);
        *list->tail = gpuChainAddress(list->cursor);
        *list->cursor = 0xC0000000;
        list->end = nullptr;
    }
    if (wordCount != 0)
        continuation = rage_A8C0(device, continuation, gpuAddress, wordCount, 0,
                                 static_cast<uint8_t*>(device) + 0x3518);
    if (field<void*>(device, 0x4FE0) != nullptr || (field<uint8_t>(device, 0x28C1) & 4) == 0) {
        const uint32_t words = static_cast<uint32_t>(
            static_cast<int32_t>(reinterpret_cast<uintptr_t>(end) - reinterpret_cast<uintptr_t>(commands)) >> 2);
        rage_A8C0(device, continuation,
                   gpuPhysicalAddress(static_cast<uint32_t>(reinterpret_cast<uintptr_t>(commands))),
                   words, flush > 1u ? 2u : 1u, static_cast<uint8_t*>(device) + 0x3518);
    }
    return 0;
}

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
        list->head = nullptr;
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
        uint32_t gpuAddress, wordCount;
        rage_A4E0(device, &gpuAddress, &wordCount);
        const uint32_t capturedWordCount = wordCount;
        if (capturedWordCount != 0) {
            void* commands = grcDevice_AllocateCommandData(device, 4, 4);
            if (commands != nullptr)
                rage_A8C0(device, commands, gpuAddress, capturedWordCount, 0,
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
