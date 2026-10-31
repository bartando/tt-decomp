#include <cstddef>
#include <cstdint>
#include <cstring>

// @ 0x82402FC0
extern "C" void swfCopyActionFunction(void* destination, const void* source) {
    auto* out = static_cast<uint8_t*>(destination);
    const auto* in = static_cast<const uint8_t*>(source);
    auto bytes = [&](size_t begin, size_t end) {
        for (size_t i = begin; i < end; ++i) out[i] = in[i];
    };
    auto words = [&](size_t begin, size_t end) {
        // Keep each load before its store, including for overlapping objects.
        // Copying encoded pointer words preserves their ptr32 representation.
        for (size_t i = begin; i < end; i += 4) {
            uint32_t word;
            std::memcpy(&word, in + i, sizeof(word));
            std::memcpy(out + i, &word, sizeof(word));
        }
    };
    // Leave dispatch (+0) and padding (+0x899..0x89B) untouched.
    bytes(4, 0x84);
    words(0x84, 0x88);
    bytes(0x88, 0x488);
    words(0x488, 0x898);
    out[0x898] = in[0x898];
    words(0x89C, 0x1CA8);
}
