// Draw-time culling of bounding spheres against the current viewport
// (called by fragDrawable_19C8_h).
#include <cmath>
#include <cstdint>

namespace rage {
void mat44TransformPoint(const float* matrix, const float* point, float* out); // @ 0x8214EA10
}
double crt_sqrt(double value); // @ 0x824301D0

// Viewport layout used here: +0x100 world-to-view matrix (16-byte aligned rows),
// +0x340/+0x344 near/far distances, +0x364..+0x380 four side planes as
// (a, b) pairs: two in x/z, two in y/z.
// Returns 0 when the sphere {x, y, z, radius} is outside, 1 when it crosses an
// edge, 2 when it is fully inside. A NaN fails every test, so it reads as inside.
// @ 0x82153D18
extern "C" int grcViewport_ClassifySphere(const void* viewport, const float* sphere) {
    const auto* vp = static_cast<const uint8_t*>(viewport);
    const auto at = [vp](unsigned offset) { return *reinterpret_cast<const float*>(vp + offset); };
    const auto* matrix = reinterpret_cast<const float*>(vp + 0x100);

    alignas(16) float center[4] = {sphere[0], sphere[1], sphere[2], 1.0f};
    alignas(16) float view[4];
    rage::mat44TransformPoint(matrix, center, view);

    // vmsum4fp128 of the first matrix row with itself: the squared x scale.
    const auto* row = reinterpret_cast<const float*>(reinterpret_cast<uintptr_t>(matrix) & ~uintptr_t(15));
    double sum = 0.0;
    for (unsigned k = 0; k < 4; ++k) {
        sum += static_cast<double>(row[k]) * row[k];
    }
    const float scaleSq = static_cast<float>(sum);
    const float z = -view[2];
    float radius = sphere[3];
    if (scaleSq < 0x1.fffeb0p-1f || scaleSq > 0x1.0000a7c5ac472p+0) {
        radius = static_cast<float>(crt_sqrt(scaleSq)) * radius;
    }

    const float nearZ = at(0x340);
    const float farZ = at(0x344);
    if (radius + z < nearZ || z - radius > farZ) {
        return 0;
    }
    const float side[4] = {
        __builtin_fmaf(at(0x364), view[0], at(0x368) * z),
        __builtin_fmaf(at(0x36C), view[0], at(0x370) * z),
        __builtin_fmaf(at(0x374), view[1], at(0x378) * z),
        __builtin_fmaf(at(0x37C), view[1], at(0x380) * z),
    };
    for (float distance : side) {
        if (distance > radius) {
            return 0;
        }
    }
    if (std::fabs(z - nearZ) < radius || std::fabs(farZ - z) < radius) {
        return 1;
    }
    for (float distance : side) {
        if (std::fabs(distance) < radius) {
            return 1;
        }
    }
    return 2;
}

// Transform a world-space sphere center and test it against the viewport's
// four side planes and near/far bounds. Returns 2 for intersection, 0 outside.
// The optional output receives the view-space z even when the sphere is outside.
// The four unused integer slots preserve Xenon's r8 placement for viewZ under ppc32 SysV.
// @ 0x82153BF8
extern "C" int grcViewport_IntersectSphere(const void* viewport, float x, float y, float z,
                                           float radius, uint32_t, uint32_t, uint32_t, uint32_t, float* viewZ) {
    const auto* vp = static_cast<const uint8_t*>(viewport);
    const auto at = [vp](unsigned offset) { return *reinterpret_cast<const float*>(vp + offset); };
    const float vx = __builtin_fmaf(at(0x220), z, __builtin_fmaf(at(0x200), x, at(0x210) * y)) + at(0x230);
    const float vy = __builtin_fmaf(at(0x224), z, __builtin_fmaf(at(0x204), x, at(0x214) * y)) + at(0x234);
    const float vz = __builtin_fmaf(at(0x228), z, __builtin_fmaf(at(0x208), x, at(0x218) * y)) + at(0x238);
    if (viewZ) {
        *viewZ = vz;
    }

    const float p0 = __builtin_fmaf(at(0x380), vz, at(0x37C) * vy);
    const float p1 = __builtin_fmaf(at(0x378), vz, at(0x374) * vy);
    const float p2 = __builtin_fmaf(at(0x370), vz, at(0x36C) * vx);
    const float p3 = __builtin_fmaf(at(0x368), vz, at(0x364) * vx);
    return radius - p0 >= 0.0f && radius - p1 >= 0.0f && radius - p2 >= 0.0f &&
           radius - p3 >= 0.0f && at(0x344) - (vz - radius) >= 0.0f &&
           (vz + radius) - at(0x340) >= 0.0f ? 2 : 0;
}
