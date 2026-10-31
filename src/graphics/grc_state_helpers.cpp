#include "grc/device_state.h"
#include "grc/image_state.hpp"
#include "rage/grc_command_stream.hpp"
#include "rage/ptr32.hpp"
#include <cstring>

extern "C" void grcDevice_SetViewport(void* device, const void* viewport); // @ 0x82355ED0
void grcDevice_FlushDirtyRegisterGroup(void* device, uint64_t dirty, uint32_t firstRegister,
                                      const uint32_t* values); // @ 0x82362658

namespace {
template<class T> T read(const void* base, uint32_t offset) {
    T value;
    std::memcpy(&value, static_cast<const uint8_t*>(base) + offset, sizeof(value));
    return value;
}
template<class T> void write(void* base, uint32_t offset, T value) {
    std::memcpy(static_cast<uint8_t*>(base) + offset, &value, sizeof(value));
}
void publish(void* device, uint32_t* cursor) {
    write(device, 0, rage::ptr32<uint32_t>(cursor));
}
uint32_t* reserve(void* device) {
    auto* cursor = rage::load_ptr32<uint32_t>(device, 0);
    auto* limit = rage::load_ptr32<uint32_t>(device, 8);
    if (reinterpret_cast<uintptr_t>(cursor) > reinterpret_cast<uintptr_t>(limit)) // ptr32-check: host - compare full translated native cursor addresses.
        cursor = static_cast<uint32_t*>(rage_A980(device));
    return cursor;
}
} // namespace

// Size the device from a surface's multisample descriptor and reset the
// scissor/viewport to the image's shared defaults.
// @ 0x823536E8 | size: 0xC4
void grc_36E8(void* device, void* surface) {
    const uint32_t descriptor = read<uint32_t>(surface, 0x30);
    const uint32_t samples = (descriptor >> 16) & 3;
    const uint32_t previous = read<uint32_t>(device, 0x2DFC) & 0xFFFE1FF8u;
    write(device, 0x2CC0, descriptor);
    write(device, 0x2DFC, previous | (samples ? 0x10000u : 0u) | ((1u << samples) - 1));
    write(device, 0x20, read<uint64_t>(device, 0x20) | UINT64_C(0x20000000));
    write(device, 0x30, read<uint64_t>(device, 0x30) | (UINT64_C(1) << 62));
    for (unsigned i = 0; i < 4; ++i)
        write(device, 0x3220 + i * 4, g_grcResolveScissor[i]);
    grcDevice_SetViewport(device, g_grcResolveViewport);
}

// Preserve the requested rectangle, optionally intersect it with the viewport,
// and retain both reserved high bits in each packed 15-bit scissor register.
// @ 0x82355E08 | size: 0xC4
void grc_5E08(void* device, const void* rect) {
    const uint32_t left = read<uint32_t>(rect, 0), top = read<uint32_t>(rect, 4);
    const uint32_t right = read<uint32_t>(rect, 8), bottom = read<uint32_t>(rect, 12);
    const uint32_t enabled = read<uint32_t>(device, 0x2EB0);
    uint32_t x0 = read<uint32_t>(device, 0x3208), y0 = read<uint32_t>(device, 0x320C);
    uint32_t x1 = x0 + read<uint32_t>(device, 0x3210), y1 = y0 + read<uint32_t>(device, 0x3214);
    write(device, 0x3220, left); write(device, 0x3224, top);
    write(device, 0x3228, right); write(device, 0x322C, bottom);
    if (enabled) {
        if (static_cast<int32_t>(x0) <= static_cast<int32_t>(left)) x0 = left;
        if (static_cast<int32_t>(y0) <= static_cast<int32_t>(top)) y0 = top;
        if (static_cast<int32_t>(x1) >= static_cast<int32_t>(right)) x1 = right;
        if (static_cast<int32_t>(y1) >= static_cast<int32_t>(bottom)) y1 = bottom;
    }
    write(device, 0x2D04, (read<uint32_t>(device, 0x2D04) & 0x80008000u) | ((y0 & 0x7FFFu) << 16) | (x0 & 0x7FFFu));
    write(device, 0x2D08, (read<uint32_t>(device, 0x2D08) & 0x80008000u) | ((y1 & 0x7FFFu) << 16) | (x1 & 0x7FFFu));
    grcDevice_SetScissorRect(device, x0, y0, x1, y1);
}

// Cache and upload one user clip plane, then mark its register group dirty.
// Copy and packet stores intentionally reload the source between each lane.
// @ 0x82356858 | size: 0xCC
void rage_6858(void* device, uint32_t index, const float* plane) {
    for (unsigned lane = 0; lane < 4; ++lane)
        write(device, 0x3230 + index * 16 + lane * 4, plane[lane]);
    uint32_t* cursor = reserve(device);
    *++cursor = 0x5C8;
    *++cursor = 0x20000;
    *++cursor = 0x30000 | ((index + 0x8E2) << 2);
    for (unsigned lane = 0; lane < 4; ++lane)
        *++cursor = read<uint32_t>(plane, lane * 4);
    publish(device, cursor);
    const uint32_t shift = (index + 46) & 127;
    const uint64_t dirty = shift < 64 ? (UINT64_C(1) << 63) >> shift : 0;
    write(device, 0x30, read<uint64_t>(device, 0x30) | dirty);
}

// Emit the resolve pass's fixed state packet and invalidate its cached groups.
// The cursor addresses the last written word, not the next free word.
// @ 0x8235DBF8 | size: 0x10C
uint32_t* grc_DBF8(void* device, uint32_t* cursor) {
    const uint32_t words[] = {0x22100, 0xFFFF, 0, 0, 0x22204, 0x10000,
                              0x10000, 0x300, 0x2312, 0xFFFF, 0xC0015000};
    for (uint32_t word : words) *++cursor = word;
    const uint32_t mask = read<uint32_t>(device, 0x32A0);
    *++cursor = mask ? mask : 0xFFFFFFFFu;
    *++cursor = 0;
    write(device, 0x28, read<uint64_t>(device, 0x28) | UINT64_C(0xE000000380000000));
    write(device, 0x30, read<uint64_t>(device, 0x30) | (UINT64_C(1) << 45));
    return cursor;
}

// Select the shader fallback mode and emit the matching GPU synchronization.
// @ 0x82363410 | size: 0xEC
void grc_3410(void* device) {
    write(device, 0x2CF4, uint32_t(0x1000));
    write(device, 0x2D94, (read<uint32_t>(device, 0x2D94) & ~7u) | 5u);
    uint32_t* cursor = reserve(device);
    *++cursor = 0x200D;
    *++cursor = read<uint32_t>(device, 0x2CF4);
    *++cursor = 0x2208;
    *++cursor = read<uint32_t>(device, 0x2D94);
    write(device, 0x20, read<uint64_t>(device, 0x20) | UINT64_C(0x10000));
    write(device, 0x28, read<uint64_t>(device, 0x28) | UINT64_C(0x20000000));
    const uint32_t words[] = {0xA31, 0x8000, 0x10A2F, 0, 0x1000, 0xC0043C00,
                              3, 0xA31, 0, 0x80000000, 8};
    for (uint32_t word : words) *++cursor = word;
    publish(device, cursor);
}

// Flush these seven register ranges in retail order. Each group re-reads its
// dirty word after the call so newly raised, unrelated flags survive.
// @ 0x82363E20 | size: 0x1C0
void grc_3E20(void* device) {
    struct Group { uint32_t offset; uint64_t mask; uint32_t shift, base, values; };
    constexpr Group groups[] = {
        {0x20, UINT64_C(0x3FFFC000), 34, 0x2000, 0x2CC0},
        {0x28, UINT64_C(0xFFFFF80000000000), 0, 0x2100, 0x2D0C},
        {0x28, UINT64_C(0x000007C000000000), 21, 0x2180, 0x2D60},
        {0x28, UINT64_C(0x0000003FFC000000), 26, 0x2200, 0x2D74},
        {0x30, UINT64_C(0x03FC0000), 38, 0x2380, 0x2E90},
        {0x28, UINT64_C(0x03FFFFE0), 38, 0x2280, 0x2DA4},
        {0x30, UINT64_C(0xFFFFFFFFFC000000), 0, 0x2300, 0x2DF8},
    };
    for (const Group& group : groups) {
        const uint64_t dirty = read<uint64_t>(device, group.offset) & group.mask;
        if (dirty) {
            const auto* values = reinterpret_cast<const uint32_t*>(static_cast<const uint8_t*>(device) + group.values);
            grcDevice_FlushDirtyRegisterGroup(device, dirty << group.shift, group.base, values);
            write(device, group.offset, read<uint64_t>(device, group.offset) & ~group.mask);
        }
    }
}

// Continue a register run across command buffers, preserving register and source
// positions. Capacity is rounded down to complete stride-sized groups.
// @ 0x823625A0 | size: 0xB8
uint32_t* grcDevice_WriteRegisterRunOverflow(void* device, uint32_t* cursor,
    uint32_t firstRegister, const uint32_t* source, uint32_t count, uint32_t stride) {
    for (;;) {
        const auto* end = rage::load_ptr32<uint32_t>(device, 4);
        const intptr_t bytes = reinterpret_cast<intptr_t>(end) - reinterpret_cast<intptr_t>(cursor); // ptr32-check: host - byte distance between translated native pointers.
        const int32_t available = static_cast<int32_t>(bytes >> 2) - 1;
        const int32_t groups = available / static_cast<int32_t>(stride);
        if (groups > 0) {
            uint32_t words = static_cast<uint32_t>(groups) * stride;
            if (words >= count) words = count;
            count -= words;
            *++cursor = ((words - 1) << 16) | firstRegister;
            for (uint32_t i = 0; i < words; ++i) *++cursor = *++source;
            firstRegister += words;
        }
        if (count == 0) return cursor;
        publish(device, cursor);
        rage_A980(device);
        // The refill's stored cursor, not its return register, is authoritative.
        cursor = rage::load_ptr32<uint32_t>(device, 0);
    }
}
