#include "rage/polygon_clip.hpp"

// The VMX interpolation rounds its multiply before adding the previous vertex.
#if defined(__clang__)
#pragma clang fp contract(off)
#elif defined(__GNUC__)
#pragma GCC optimize("fp-contract=off")
#endif

namespace rage {

// @ 0x82147A88
void clipPolygonToPlane(void* /*context*/, int32_t vertexCount, const float (*vertices)[4],
                        int32_t* outputCount, float (*output)[4], const float* plane) {
    // Misnamed SinglesNetworkClient_7A88_2hr in the generated symbol map.
    // Sutherland–Hodgman: retain the half-space dot(plane.xyz, vertex.xyz) + plane.w <= 0.
    // The caller at 0x82147D18 clips a polygon successively against six planes.
    *outputCount = 0;
    if (vertexCount <= 0) {
        return;
    }

    float previous[4];
    __builtin_memcpy(previous, vertices[vertexCount - 1], sizeof(previous));

    for (int32_t i = 0; i < vertexCount; ++i) {
        float current[4];
        __builtin_memcpy(current, vertices[i], sizeof(current));

        // The original uses different addition orders at the two endpoints:
        // previous = (nx*x + ny*y) + nz*z; current = nx*x + (ny*y + nz*z).
        float previousY = plane[1] * previous[1];
        float previousXY = __builtin_fmaf(plane[0], previous[0], previousY);
        float previousDot = __builtin_fmaf(plane[2], previous[2], previousXY);
        float previousDistance = previousDot + plane[3];
        float currentZ = plane[2] * current[2];
        float currentYZ = __builtin_fmaf(plane[1], current[1], currentZ);
        float currentDot = __builtin_fmaf(plane[0], current[0], currentYZ);
        float currentDistance = currentDot + plane[3];

        // Ordered <= also rejects NaNs, as fcmpu followed by bgt/bso does.
        bool currentInside = currentDistance <= 0.0f;
        bool previousInside = previousDistance <= 0.0f;
        if (currentInside != previousInside) {
            float fraction = previousDistance / (previousDistance - currentDistance);
            int32_t index = (*outputCount)++;
            for (int lane = 0; lane < 4; ++lane) {
                float delta = current[lane] - previous[lane];
                float scaled = delta * fraction;
                output[index][lane] = previous[lane] + scaled;
            }
        }
        if (currentInside) {
            __builtin_memcpy(output[(*outputCount)++], current, sizeof(current));
        }
        __builtin_memcpy(previous, current, sizeof(previous));
    }
}

} // namespace rage
