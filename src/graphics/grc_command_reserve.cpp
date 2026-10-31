#include "grc/gpu_hang.hpp"
#include "rage/grc_command_stream.hpp"
#include "rage/ptr32.hpp"
#include "platform/video_imports.h"

extern "C" void* g_sda_base; // @ 0x82600000 — native root of the game thread state
extern "C" uint32_t xe_GetCurrentThreadId(); // @ 0x82566B78

namespace {
template <class T> T& commandField(void* device, uint32_t offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(device) + offset);
}
using ReserveCommands = void*(void* context, void* device, uint32_t kind,
                               uint32_t* bytes, uint32_t alignment);
}

// Enter the emergency command buffer. A title device stores its emergency
// buffer pointer in the imported global device; the system process embeds it.
// @ 0x82359D38 | size: 0x84
extern "C" void grcDevice_UseEmergencyCommandBuffer(void* device) {
    uint8_t* start;
    if (KeGetCurrentProcessType() == 2) {
        start = static_cast<uint8_t*>(device) + 0x3D1C;
    } else {
        void* globalDevice = KeGetCurrentProcessType() == 2
            ? *__imp_VdGlobalXamDevice : *__imp_VdGlobalDevice;
        start = rage::load_ptr32<uint8_t>(globalDevice, 0x3D1C);
    }
    commandField<rage::ptr32<uint8_t>>(device, 0) = start;
    commandField<rage::ptr32<uint8_t>>(device, 4) = start + 0x12C0;
    commandField<rage::ptr32<uint8_t>>(device, 8) = start + 0x1220;
    commandField<uint8_t>(device, 0x28C1) |= 0x80;
}

// Reserve a fresh command window, falling back to the emergency buffer when
// allocation fails. The pending fence slot is chosen after the callbacks.
// @ 0x8235A150 | size: 0x11C
extern "C" void* rage_A150(void* device, uint32_t words) {
    if (commandField<uint8_t>(device, 0x28C1) & 0x80) {
        grcDevice_UseEmergencyCommandBuffer(device);
        return nullptr;
    }
    uint32_t bytes = words == 0 ? 0 : (words + 12) * 4;
    auto* reserve = rage::load_ptr32<ReserveCommands>(device, 0x3544);
    void* context = rage::load_ptr32<void>(device, 0x3548);
    auto* result = static_cast<uint8_t*>(reserve(context, device, 0, &bytes, 32));
    if (!result) {
        grcDevice_UseEmergencyCommandBuffer(device);
    } else {
        commandField<rage::ptr32<uint8_t>>(device, 0x36CC) = result;
        commandField<uint32_t>(device, 0x36C0) = 0;
        commandField<uint32_t>(device, 0x36D0) = 0;
        auto* start = result - 4;
        // The original rounds the callback's byte count down to whole words,
        // reserves twelve words, then keeps 0xA0 bytes behind the hard limit.
        auto* end = start + static_cast<int32_t>(((bytes >> 2) - 12) * 4);
        commandField<rage::ptr32<uint8_t>>(device, 0) = start;
        commandField<rage::ptr32<uint8_t>>(device, 4) = end;
        commandField<rage::ptr32<uint8_t>>(device, 8) = end - 0xA0;
    }
    const uint32_t fenceOffset = commandField<uint32_t>(device, 0x5070) & 1 ? 0x36DC : 0x36D8;
    uint32_t fence = commandField<uint32_t>(device, fenceOffset);
    xe_GetCurrentThreadId();
    if (fence != 0) rage_AA78(device, &fence);
    commandField<uint32_t>(device, fenceOffset) = 0;
    return result;
}

// Wait for a command fence relative to the current wrap sequence. Equal-to-
// producer fences force submission unless an alternate command path is active.
// @ 0x8235AA78 | size: 0xE8
extern "C" void rage_AA78(void* device, uint32_t* fence) {
    const auto pending = [device, fence]() {
        const uint32_t producer = commandField<uint32_t>(device, 0x289C);
        auto* consumer = rage::load_ptr32<volatile uint32_t>(device, 0x2890);
        return producer - *fence < producer - *consumer;
    };
    if (!pending()) return;
    if (*fence == commandField<uint32_t>(device, 0x289C)) {
        if (commandField<uint32_t>(device, 0x34E0) != 0) return;
        rage_A980(device);
    }
    if (!pending()) return;
    auto* consumer = rage::load_ptr32<volatile uint32_t>(device, 0x2890);
    grcGpuHangState hang;
    hang.device = device;
    hang.lastQueueHead = *consumer;
    // The assembly deliberately samples the consumer twice before the loop.
    const uint32_t producer = commandField<uint32_t>(device, 0x289C);
    uint32_t lag = producer - *consumer;
    const auto* thread = rage::load_ptr32<uint8_t>(g_sda_base, 0x100);
    hang.lastGpuTick = *reinterpret_cast<const uint32_t*>(thread + 0x58);
    while (commandField<uint32_t>(device, 0x289C) - *fence < lag) {
        if (D3DDeviceXenon_ReportGPUHang(&hang) == 0) return;
        consumer = rage::load_ptr32<volatile uint32_t>(device, 0x2890);
        lag = commandField<uint32_t>(device, 0x289C) - *consumer;
    }
}

// Emit the synchronization packet, retire the captured fence, then wait for
// the driver's queued-command flag to clear. The flag is shared with the GPU
// command worker and must be loaded on every iteration.
// @ 0x8235AD98 | size: 0x88
extern "C" void rage_AD98(void* device) {
    auto* cursor = rage::load_ptr32<uint32_t>(device, 0);
    auto* limit = rage::load_ptr32<uint32_t>(device, 8);
    if (cursor > limit) cursor = static_cast<uint32_t*>(rage_A980(device));
    *++cursor = 0x5C8;
    *++cursor = 0x20000;
    uint32_t fence = commandField<uint32_t>(device, 0x289C);
    commandField<rage::ptr32<uint32_t>>(device, 0) = cursor;
    xe_GetCurrentThreadId();
    if (fence != 0) rage_AA78(device, &fence);
    while (commandField<volatile uint32_t>(device, 0x28FC) != 0) {}
}
