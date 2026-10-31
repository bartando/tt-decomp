// Creature pose snapshots and worker reset, recovered from the original PPC.
#include <cstdint>
#include <cstring>

namespace {
float flushPoseFloat(float value) {
    uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        std::memcpy(&value, &bits, sizeof(value));
    }
    return value;
}

// VMX dot3 accumulates the three products before rounding to a float.
float poseDot3(const float* vector, const float* matrix, unsigned column) {
    double sum = 0.0;
    for (unsigned axis = 0; axis < 3; ++axis)
        sum += double(flushPoseFloat(vector[axis])) * flushPoseFloat(matrix[axis * 4 + column]);
    return flushPoseFloat(static_cast<float>(sum));
}
}

// Copy the current pose, compensating translation for each bone's rest position.
// LocomotionState_CD70_g @ 0x8214CD70 | size: 0x118
extern "C" void LocomotionState_CD70_g(void* skeleton, void* poseSnapshot) {
    const auto* bytes = static_cast<const uint8_t*>(skeleton);
    const auto* data = *reinterpret_cast<const uint8_t* const*>(bytes + 4);
    const auto* banks = *reinterpret_cast<const uint8_t* const* const*>(bytes + 0x18);
    const unsigned bank = *reinterpret_cast<const uint16_t*>(bytes + 0x22);
    const auto* matrices = banks[bank * 2];
    const int count = *reinterpret_cast<const uint16_t*>(data + 0x0C);
    auto* output = static_cast<uint8_t*>(poseSnapshot);
    for (int bone = count - 1; bone >= 0; --bone) {
        const auto* overrideData = *reinterpret_cast<const uint8_t* const*>(bytes + 0x24);
        const auto* rest = overrideData
            ? *reinterpret_cast<const uint8_t* const*>(overrideData + 4) + bone * 16
            : *reinterpret_cast<const uint8_t* const*>(data) + bone * 0xC0 + 0x50;
        alignas(16) float restPosition[4];
        std::memcpy(restPosition, rest, sizeof(restPosition));
        const auto* source = matrices + bone * 64;
        auto* target = output + bone * 64;
        // Preserve the original's row-by-row load/store order for overlaps.
        for (unsigned row = 0; row < 3; ++row)
            std::memcpy(target + row * 16, source + row * 16, 16);
        const auto* matrix = reinterpret_cast<const float*>(source);
        const float x = poseDot3(restPosition, matrix, 0);
        const float y = poseDot3(restPosition, matrix, 1);
        const float z = poseDot3(restPosition, matrix, 2);
        const float offsets[4] = {x, y, z, x};
        alignas(16) float translation[4];
        std::memcpy(translation, source + 0x30, sizeof(translation));
        auto* targetTranslation = reinterpret_cast<float*>(target + 0x30);
        for (unsigned lane = 0; lane < 4; ++lane)
            targetTranslation[lane] = flushPoseFloat(flushPoseFloat(translation[lane]) - offsets[lane]);
    }
}
