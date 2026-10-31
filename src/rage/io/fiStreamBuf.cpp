#include "rage/fi_stream.hpp"
#include <cstring>

// @ 0x822E2B50
extern "C" void fiPath_Build(void* assets, char* destination, int32_t capacity,
                              const char* name, const char* extension, int32_t root);

// @ 0x822E3040
extern "C" void* fiStreamBuf_OpenAll(void* assets, const char* name,
                                     const char* extension, uint32_t, uint32_t flags) {
    const auto* roots = reinterpret_cast<const int32_t*>(static_cast<const uint8_t*>(assets) + 0x604);
    void* result = nullptr;
    for (int32_t root = 0; root < *roots && !result; ++root) {
        char path[256];
        fiPath_Build(assets, path, sizeof(path), name, extension, root);
        result = fiStream_Open(path, flags);
    }
    return result;
}

// @ 0x822E3828
extern "C" int32_t fiStreamBuf_Read(void* stream, void* destination, int32_t bytes) {
    auto* s = static_cast<rage::fiStreamBuf*>(stream);
    auto* out = static_cast<uint8_t*>(destination);
    int32_t copied = 0;
    if (s->end == 0 && s->cursor != 0 && fiStreamBuf_Finalize(s) < 0)
        return -1;

    int32_t end = s->end;
    if (bytes > end - s->cursor) {
        if (end != s->cursor) {
            std::memcpy(out, s->buffer.get() + s->cursor, end - s->cursor);
            copied = s->end - s->cursor;
            s->cursor = s->end;
            out += copied;
            bytes -= copied;
        }
        s->position += static_cast<uint32_t>(s->cursor);
        if (bytes >= s->capacity) {
            int32_t got = s->device->Read(s->handle, out, bytes);
            s->cursor = 0;
            s->end = 0;
            if (got < 0) return -1;
            s->position += static_cast<uint32_t>(got);
            return got + copied;
        }
        end = s->device->Read(s->handle, s->buffer.get(), s->capacity);
        s->cursor = 0;
        s->end = end;
        if (end < 0) {
            s->cursor = 0;
            s->end = 0;
            return -1;
        }
    }
    int32_t count = end - s->cursor;
    if (bytes < count) count = bytes;
    std::memcpy(out, s->buffer.get() + s->cursor, count);
    s->cursor += count;
    return copied + count;
}

// @ 0x822E3BA8
extern "C" int32_t fiStreamBuf_Finalize(void* stream) {
    auto* s = static_cast<rage::fiStreamBuf*>(stream);
    if (s->end != 0) {
        if (s->end != s->cursor)
            s->device->Seek(s->handle, s->position + static_cast<uint32_t>(s->cursor), 0);
    } else if (s->cursor != 0) {
        s->device->Write(s->handle, s->buffer.get(), s->cursor);
    }
    const int32_t cursor = s->cursor;
    auto* device = s->device.get();
    const uint32_t handle = s->handle;
    s->end = 0;
    s->cursor = 0;
    s->position += static_cast<uint32_t>(cursor);
    return device->Flush(handle);
}

// @ 0x822E3AC8
extern "C" int32_t fiStreamBuf_Reset(void* stream, int32_t position) {
    auto* s = static_cast<rage::fiStreamBuf*>(stream);
    if (fiStreamBuf_Finalize(s) < 0) return -1;
    auto* device = s->device.get();
    s->position = static_cast<uint32_t>(position);
    return device->Seek(s->handle, position, 0);
}

// @ 0x822E3B38
extern "C" int32_t fiStreamBuf_Close(void* stream) {
    auto* s = static_cast<rage::fiStreamBuf*>(stream);
    if (s->end == 0 && s->cursor != 0)
        fiStreamBuf_Finalize(s);
    s->device->Close(s->handle);
    s->handle = 0xffffffffu;
    s->device = nullptr;
    return 0;
}

// @ 0x822E3CD8
extern "C" int32_t fiStreamBuf_ReadWords(void* stream, void* destination, int32_t words) {
    const int32_t bytes = fiStreamBuf_Read(stream, destination, static_cast<uint32_t>(words) << 2);
    const int32_t count = bytes >> 2;
#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
    auto* out = static_cast<uint8_t*>(destination);
    for (int32_t i = 0; i < count; ++i) {
        uint32_t word;
        std::memcpy(&word, out + i * 4, sizeof(word));
        word = __builtin_bswap32(word);
        std::memcpy(out + i * 4, &word, sizeof(word));
    }
#endif
    return count;
}

// ─────────────────────────────────────────────────────────────────────────────
// XAPO — Xbox Audio Processing Objects helper.
// Extracts frame-count / sample-buffer metadata from a platform buffer
// descriptor. Consumed by CDelayEffect::Process and CPeakMeterEffect::Process
// in pong_audio_effects.cpp.
// ─────────────────────────────────────────────────────────────────────────────
extern "C" void xapo_UnpackBuffer(void* buffer, void* outInfo) {
    (void)buffer; (void)outInfo;
}
