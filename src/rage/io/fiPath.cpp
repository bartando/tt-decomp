#include "rage/ptr32.hpp"
#include <cstdint>
#include <cstring>

extern "C" {
// @ 0x82433A40
int _stricmp(const char*, const char*);
// @ 0x8240E6D0
void rage_DebugLog(const char*, ...);
// @ 0x825D06A0
extern rage::ptr32<void> g_fiLongNameOptionValue; // @ 0x825D06A0
}

// @ 0x820F0888
extern "C" void rage_strcat_bounded(char* destination, const char* source, int32_t capacity) {
    size_t length = destination ? std::strlen(destination) : 0;
    char* out = destination + length;
    int32_t remaining = static_cast<uint32_t>(capacity) - length - 1;
    while (*source && remaining > 0) {
        *out++ = *source++;
        --remaining;
    }
    *out = 0;
}

// @ 0x822E2A20
extern "C" int32_t fiPath_RemoveParentDir(char* path) {
    char* dot = std::strchr(path, '.');
    if (!dot || dot <= path || (dot[-1] != '/' && dot[-1] != '\\') ||
        dot[1] != '.' || (dot[2] != '/' && dot[2] != '\\'))
        return 0;
    char* parent = dot;
    while (parent > path + 2 && parent[-2] != '/' && parent[-2] != '\\')
        --parent;
    std::memmove(parent - 2, dot + 2, std::strlen(dot + 2) + 1);
    return 1;
}

// @ 0x822E2830 — append name/extension, normalize separators and check basename.
extern "C" void fiPath_AppendName(void*, char* out, int32_t capacity,
                                   const char* name, const char* extension) {
    if (capacity > 0) rage_strcat_bounded(out, name, capacity);
    else *out = 0;
    if (extension && *extension) {
        const char* dot = std::strrchr(name, '.');
        if (!dot || _stricmp(std::strrchr(name, '.') + 1, extension) != 0) {
            if (capacity > 0) rage_strcat_bounded(out, ".", capacity);
            else *out = 0;
            if (capacity > 0) rage_strcat_bounded(out, extension, capacity);
            else *out = 0;
        }
    }
    char* write = out;
    for (const char* read = out; *read; ++read) {
        *write = *read == '\\' ? '/' : *read;
        if (write < out + 2 || *write != '/' || write[-1] != '/') ++write;
    }
    *write = 0;
    char* slash = std::strrchr(out, '/');
    if (slash && std::strlen(slash + 1) > 42) {
        // The original deliberately replaces the slash as well as the basename.
        if (g_fiLongNameOptionValue) {
            rage_DebugLog("Filename '%s' is too long!", slash + 1);
            std::memcpy(slash, "FilenameTooLong", 16);
        } else {
            rage_DebugLog("Filename '%s' is too long!", slash + 1);
        }
    }
}

namespace {
bool relative(const char* name) {
    return !name || (name[0] != '/' && name[0] != '\\' && !std::strchr(name, ':'));
}
void copyAssetPathPrefix(char* out, const char* source, int32_t capacity) {
    for (int32_t remaining = capacity - 1; remaining > 0 && *source; --remaining)
        *out++ = *source++;
    *out = 0;
}
}

// @ 0x822E2B50
extern "C" void fiPath_Build(void* assets, char* out, int32_t capacity,
                              const char* name, const char* extension, int32_t root) {
    const auto* base = static_cast<const uint8_t*>(assets);
    const auto* depth = reinterpret_cast<const int32_t*>(base + 0x600);
    if (relative(name)) {
        copyAssetPathPrefix(out, reinterpret_cast<const char*>(base + root * 128), capacity);
        if (name[0] == '$') {
            name += 2;
        } else if (*depth != 0) {
            const char* folder = reinterpret_cast<const char*>(base + (*depth + 3) * 128);
            if (!relative(folder))
                copyAssetPathPrefix(out, reinterpret_cast<const char*>(base + (*depth + 3) * 128), capacity);
            else if (capacity > 0)
                rage_strcat_bounded(out, reinterpret_cast<const char*>(base + (*depth + 3) * 128), capacity);
            else *out = 0;
        }
    } else *out = 0;
    while (fiPath_RemoveParentDir(out)) {}
    fiPath_AppendName(assets, out, capacity, name, extension);
}
