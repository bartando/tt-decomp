#include "rage/ptr32.hpp"
#include "rage/swf_state.hpp"
#include "grc/image_state.hpp"
#include <cmath>
#include <cstdint>
#include <cstring>

namespace rage {
namespace {
struct Gradient {
    float matrix[6];
    uint8_t count;
    uint8_t radial;
    uint8_t _pad1A[2];
    ptr32<const uint8_t> ratios;
    ptr32<const uint32_t> colors;
};
static_assert(sizeof(Gradient) == 0x24);
}

// @ 0x824060B8
uint32_t swfSampleGradient(const void* gradient, float x, float y) {
    const auto* fill = static_cast<const Gradient*>(gradient);
    const float ax = fill->matrix[0] * x;
    const float dy = fill->matrix[3] * y;
    const float u = std::fma(fill->matrix[2], y, ax) + fill->matrix[4];
    const float v = std::fma(fill->matrix[1], x, dy) + fill->matrix[5];
    float position;
    if (fill->radial != 0) {
        const float yy = v * v;
        const float radius = static_cast<float>(std::sqrt(static_cast<double>(std::fma(u, u, yy))));
        position = radius * 0x1.fdfffep-7f; // image 0x82079BEC
    } else {
        position = (u + 16384.0f) * 0x1.fep-8f; // image 0x82079BE8 / 0x82079BE4
    }
    if (position < 0.0f) position = 0.0f;
    else if (position > 255.0f) position = 255.0f;
    // fctiwz gives INT_MIN for NaN; only its low byte is used.
    const uint32_t index = position == position ? static_cast<uint32_t>(position) : 0;
    const uint32_t* colors = fill->colors.get();
    const uint8_t* ratios = fill->ratios.get();
    for (int i = 0; i < int(fill->count) - 1; ++i) {
        if (index < ratios[i] || index > ratios[i + 1]) continue;
        const uint32_t span = uint8_t(ratios[i + 1] - ratios[i]);
        if (span == 0) __builtin_trap();
        const uint32_t offset = uint8_t(index - ratios[i]);
        uint32_t result = 0;
        for (unsigned shift = 0; shift < 32; shift += 8) {
            const uint32_t start = (colors[i] >> shift) & 255;
            const uint32_t end = (colors[i + 1] >> shift) & 255;
            // Retail uses unsigned division even for decreasing channels and
            // packs the full quotient, allowing carries into adjacent bytes.
            result |= (start + ((end - start) * offset) / span) << shift;
        }
        return result;
    }
    return colors[0];
}

// @ 0x82406290
void swfApplyStrokeStyle(const void* stroke, const void* transform) {
    g_swfBindFontTexture(nullptr);
    const auto* state = static_cast<const uint8_t*>(transform);
    const auto* multiply = reinterpret_cast<const int8_t*>(state + 0x38);
    const auto* add = reinterpret_cast<const int8_t*>(state + 0x3C);
    uint32_t color;
    std::memcpy(&color, static_cast<const uint8_t*>(stroke) + 4, sizeof(color));
    uint32_t transformed = 0;
    for (unsigned channel = 0; channel < 4; ++channel) {
        const unsigned shift = channel == 3 ? 24 : 16 - channel * 8;
        int value = (int((color >> shift) & 255) * multiply[channel] >> 6) + int(add[channel]) * 4;
        value = value < 0 ? 0 : value > 255 ? 255 : value;
        if (channel == 3) value = value * state[0x47] / 255;
        transformed |= uint32_t(value) << shift;
    }
    g_fxCurrentColor = transformed;
}
}
