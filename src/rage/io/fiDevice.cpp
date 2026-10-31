#include "rage/fi_device_internal.hpp"
#include <cstring>

extern "C" void rage_DebugLog(const char*, ...); // @ 0x8240E6D0

// @ 0x822E1218 — ASCII case folding and slash normalization over a prefix.
extern "C" int32_t fiDevice_ComparePrefix(const char* left, const char* right, uint32_t bytes) {
    uint32_t a = 0, b = 0;
    while (bytes != 0) {
        a = static_cast<uint8_t>(*left++);
        b = static_cast<uint8_t>(*right++);
        if (a >= 'A' && a <= 'Z') a += 'a' - 'A';
        if (b >= 'A' && b <= 'Z') b += 'a' - 'A';
        if (a == '\\') a = '/';
        if (b == '\\') b = '/';
        --bytes;
        if (a == 0 || a != b) break;
    }
    return a - b;
}

// @ 0x822E12A0
extern "C" void* fiDevice_GetDevice(const char* path, uint32_t flags) {
    if (std::strncmp(path, "memory:", 7) == 0) return lbl_825D0074;
    if (std::strncmp(path, "tcpip:", 6) == 0) return lbl_825D06C4;
    if (std::strncmp(path, "cache:", 6) == 0) return lbl_825D0070;
    if (std::strncmp(path, "game:", 5) == 0) return lbl_825D0070;

    auto* entries = lbl_8262F368.entries.get();
    const int32_t count = lbl_8262F368.count;
    int32_t best = -1;
    int32_t longest = 0;
    for (int32_t i = 0; i < count; ++i) {
        const uint16_t length = entries[i].prefixLength;
        if (fiDevice_ComparePrefix(entries[i].prefix, path, length) == 0 && length > longest) {
            longest = length;
            best = i;
        }
    }
    if (best != -1) {
        rage::fiStreamDevice* result = nullptr;
        const int32_t deviceCount = entries[best].count;
        if (deviceCount == 1) {
            result = entries[best].devices.get()[0].get();
        } else {
            for (int32_t index = deviceCount - 1; index >= 0; --index) {
                auto* device = entries[best].devices.get()[index].get();
                const int32_t handle = device->Open(path, 1);
                entries = lbl_8262F368.entries.get();
                if (handle != -1) {
                    entries[best].devices.get()[index]->Close(handle);
                    entries = lbl_8262F368.entries.get();
                    result = entries[best].devices.get()[index].get();
                    break;
                }
            }
        }
        if (static_cast<uint8_t>(flags) == 0 && entries[best].readOnly != 0)
            return nullptr;
        return result;
    }
    auto* fallback = lbl_825C481C.get();
    if (!fallback)
        rage_DebugLog("fiDevice::GetDevice - Filename '%s' not in mount list, no default device", path);
    if (static_cast<uint8_t>(flags) == 0 && g_fiFallbackReadOnly != 0)
        return nullptr;
    return fallback;
}
