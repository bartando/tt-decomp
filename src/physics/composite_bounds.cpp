#include "composite_bounds.hpp"
#include "rage/ptr32.hpp"
#include <cmath>
#include <cstring>

extern "C" {
extern const uint32_t lbl_82619BD0[4]; // @ 0x82619BD0 — homogeneous W
extern const uint32_t lbl_82619BE0[4]; // @ 0x82619BE0 — XYZ mask
extern const float lbl_82619BF0[4]; // @ 0x82619BF0 — rsqrt sentinel
extern const float lbl_82606750[4]; // @ 0x82606750 — replacement vector
extern const float lbl_825CB7C0[4]; // @ 0x825CB7C0 — one vector
extern const float lbl_825CB7D0[4]; // @ 0x825CB7D0 — half vector
}
double crt_sqrt(double value); // @ 0x824301D0

namespace {
float flushCompositeVmx(float value) {
    uint32_t bits;
    std::memcpy(&bits, &value, 4);
    if ((bits & 0x7f800000u) == 0) {
        bits &= 0x80000000u;
        std::memcpy(&value, &bits, 4);
    }
    return value;
}
float multiplyCompositeVmx(float a, float b) { return flushCompositeVmx(flushCompositeVmx(a) * flushCompositeVmx(b)); }
float addCompositeVmx(float a, float b) { return flushCompositeVmx(flushCompositeVmx(a) + flushCompositeVmx(b)); }
float subtractCompositeVmx(float a, float b) { return flushCompositeVmx(flushCompositeVmx(a) - flushCompositeVmx(b)); }
float dotCompositeVmx(const float* a, const float* b, unsigned count) {
    double sum = 0.0;
    for (unsigned i = 0; i < count; ++i)
        sum += double(flushCompositeVmx(a[i])) * flushCompositeVmx(b[i]);
    return flushCompositeVmx(float(sum));
}
float compositeMaskLane(float value, uint32_t andBits, uint32_t orBits = 0) {
    uint32_t bits;
    std::memcpy(&bits, &value, 4);
    bits = (bits & andBits) | orBits;
    std::memcpy(&value, &bits, 4);
    return value;
}
const float* alignedVector(const float* pointer) {
    // ptr32-check: host — align an already translated native address for lvx.
    return reinterpret_cast<const float*>(reinterpret_cast<uintptr_t>(pointer) & ~uintptr_t(15));
}
float refinedLength(const float* delta) {
    const float squared = dotCompositeVmx(delta, delta, 3);
    const float estimate = flushCompositeVmx(float(1.0 / std::sqrt(double(squared))));
    const float inverse = estimate == flushCompositeVmx(lbl_82619BF0[0]) ? lbl_82606750[0] : estimate;
    const float squareInverse = multiplyCompositeVmx(inverse, inverse);
    const float halfInverse = multiplyCompositeVmx(lbl_825CB7D0[0], inverse);
    const float error = flushCompositeVmx(-subtractCompositeVmx(multiplyCompositeVmx(squared, squareInverse), lbl_825CB7C0[0]));
    const float refined = addCompositeVmx(multiplyCompositeVmx(error, halfInverse), inverse);
    return multiplyCompositeVmx(squared, refined);
}
float transformedCorner(const float* child, const float* matrix, unsigned axis, bool upper) {
    float terms[3];
    for (unsigned component = 0; component < 3; ++component) {
        const float a = matrix[component * 4 + axis] * child[4 + component];
        const float b = matrix[component * 4 + axis] * child[8 + component];
        const float difference = b - a;
        terms[component] = upper ? (difference >= 0.0f ? b : a)
                                 : (difference >= 0.0f ? a : b);
    }
    // The X and Y/Z sums use different scalar rounding orders in the image.
    if (axis == 0) return ((terms[2] + terms[1]) + terms[0]) + matrix[12];
    return ((matrix[12 + axis] + terms[2]) + terms[1]) + terms[0];
}
}

namespace rage {
// @ 0x8228ECB0
float phBoundComposite_ComputeRadius(void* bound, const float* partMatrices, const float* centroid) {
    const auto* bytes = static_cast<const uint8_t*>(bound);
    const int count = *reinterpret_cast<const uint16_t*>(bytes + 0x82);
    if (count == 0) return 0.0f;
    const auto* children = load_ptr32<ptr32<float>>(bound, 0x70);
    float radius = 0.0f;
    for (int index = count - 1; index >= 0; --index) {
        const float* child = children[index].get();
        if (!child) continue;
        const float* matrix = alignedVector(partMatrices + index * 16);
        const float* childCenter = alignedVector(child + 12);
        const float* center = alignedVector(centroid);
        float homogeneous[4];
        for (unsigned lane = 0; lane < 4; ++lane)
            homogeneous[lane] = compositeMaskLane(childCenter[lane], lbl_82619BE0[lane], lbl_82619BD0[lane]);
        float delta[4];
        for (unsigned axis = 0; axis < 3; ++axis) {
            const float column[4] = {matrix[axis], matrix[4 + axis], matrix[8 + axis], matrix[12 + axis]};
            delta[axis] = subtractCompositeVmx(dotCompositeVmx(homogeneous, column, 4), center[axis]);
        }
        const float candidate = child[2] + refinedLength(delta);
        const float difference = radius - candidate;
        radius = difference >= 0.0f ? radius : candidate;
    }
    return radius;
}

// @ 0x8228E888
void phBoundComposite_RebuildExtents(void* bound) {
    auto* bytes = static_cast<uint8_t*>(bound);
    auto* values = reinterpret_cast<float*>(bound);
    for (unsigned axis = 0; axis < 3; ++axis) {
        values[8 + axis] = 0x1.fffffep127f;
        values[4 + axis] = -0x1.fffffep127f;
    }
    const int count = *reinterpret_cast<uint16_t*>(bytes + 0x82);
    const auto* children = load_ptr32<ptr32<float>>(bound, 0x70);
    bool any = false;
    for (int index = count - 1; index >= 0; --index) {
        const float* child = children[index].get();
        if (!child) continue;
        const auto* matrices = load_ptr32<float>(bound, 0x78);
        const float* matrix = matrices + index * 16;
        for (unsigned axis = 0; axis < 3; ++axis) {
            const float corner = transformedCorner(child, matrix, axis, false);
            const float old = values[8 + axis];
            const float difference = old - corner;
            values[8 + axis] = difference >= 0.0f ? corner : old;
        }
        for (unsigned axis = 0; axis < 3; ++axis) {
            const float corner = transformedCorner(child, matrix, axis, true);
            const float old = values[4 + axis];
            const float difference = old - corner;
            values[4 + axis] = difference >= 0.0f ? old : corner;
        }
        any = true;
    }
    if (!any) {
        std::memset(bytes + 0x20, 0, 16);
        std::memset(bytes + 0x10, 0, 16);
    }
    bool displaced = false;
    for (unsigned lane = 0; lane < 4; ++lane) {
        values[12 + lane] = multiplyCompositeVmx(addCompositeVmx(values[4 + lane], values[8 + lane]), lbl_825CB7D0[lane]);
        displaced |= flushCompositeVmx(compositeMaskLane(values[12 + lane], lbl_82619BE0[lane])) != 0.0f;
    }
    bytes[5] = displaced;
    const float lowerSquared = dotCompositeVmx(values + 8, values + 8, 3);
    const float upperSquared = dotCompositeVmx(values + 4, values + 4, 3);
    const float difference = upperSquared - lowerSquared;
    const float squared = difference >= 0.0f ? upperSquared : lowerSquared;
    values[3] = float(crt_sqrt(squared));
}

// @ 0x8228F3E0
void phBoundComposite_Symmetrize(void* bound) {
    auto* values = static_cast<float*>(bound);
    for (unsigned axis = 0; axis < 3; ++axis) {
        const float upper = values[4 + axis];
        const float lower = values[8 + axis];
        // Unordered and equal magnitudes retain the upper side.
        if (__builtin_fabsf(upper) < __builtin_fabsf(lower))
            values[4 + axis] = -lower;
        else
            values[8 + axis] = -upper;
    }
    float width[4];
    for (unsigned lane = 0; lane < 4; ++lane)
        width[lane] = subtractCompositeVmx(values[4 + lane], values[8 + lane]);
    const float radius = refinedLength(width) * 0.5f;
    values[2] = radius;
    values[3] = radius;
    // The original deliberately leaves the centroid-present byte at +5 alone.
    std::memset(static_cast<uint8_t*>(bound) + 0x30, 0, 16);
}

}
