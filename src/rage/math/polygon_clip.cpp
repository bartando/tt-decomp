#include "rage/polygon_clip.hpp"

// The VMX interpolation rounds its multiply before adding the previous vertex.
#if defined(__clang__)
#pragma clang fp contract(off)
#elif defined(__GNUC__)
#pragma GCC optimize("fp-contract=off")
#endif

extern "C" const float lbl_8202D110; // @ 0x8202D110

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

// @ 0x82147BF8
void clipLineToPlane(void* /*context*/, int32_t vertexCount, const float (*vertices)[4],
                     int32_t* outputCount, float (*output)[4], const float* plane) {
    *outputCount = vertexCount;
    float firstZ = vertices[0][2] * plane[2];
    float firstYZ = __builtin_fmaf(vertices[0][1], plane[1], firstZ);
    float firstDistance = __builtin_fmaf(vertices[0][0], plane[0], firstYZ) + plane[3];
    float secondZ = vertices[1][2] * plane[2];
    float secondYZ = __builtin_fmaf(vertices[1][1], plane[1], secondZ);
    float secondDistance = __builtin_fmaf(plane[0], vertices[1][0], secondYZ) + plane[3];

    bool firstInside = firstDistance <= lbl_8202D110;
    bool secondInside = secondDistance <= lbl_8202D110;
    if (!firstInside && !secondInside) {
        *outputCount = 0;
        return;
    }
    if (firstInside && secondInside) {
        __builtin_memcpy(output, vertices, 2 * sizeof(*output));
        return;
    }
    float fraction = firstDistance / (firstDistance - secondDistance);
    for (int lane = 0; lane < 4; ++lane) {
        float delta = vertices[1][lane] - vertices[0][lane];
        float scaled = delta * fraction;
        float intersection = vertices[0][lane] + scaled;
        output[0][lane] = firstInside ? vertices[0][lane] : intersection;
        output[1][lane] = secondInside ? vertices[1][lane] : intersection;
    }
}

// @ 0x82147D18
void clipPolygonToFrustum(void* context, int32_t /*unusedCount*/, const float (*vertices)[4],
                          int32_t* outputCount, float (*output)[4], const float (*planes)[4],
                          const float* referencePoint) {
    alignas(16) float scratch[16][4];
    __builtin_memcpy(scratch, vertices, 4 * sizeof(scratch[0]));
    int32_t count = 4;
    for (int plane = 0; plane < 6; ++plane) {
        if (referencePoint) {
            // vmsum3fp128 rounds the dot product to float before subtracting plane.w.
            float dot = static_cast<float>(static_cast<double>(planes[plane][0]) * referencePoint[0] +
                                           static_cast<double>(planes[plane][1]) * referencePoint[1] +
                                           static_cast<double>(planes[plane][2]) * referencePoint[2]);
            if (dot - planes[plane][3] > 0.0f) {
                continue;
            }
        }
        clipPolygonToPlane(context, count, scratch, outputCount, output, planes[plane]);
        count = *outputCount;
        if (count == 0) {
            return;
        }
        if (count > 0) {
            __builtin_memcpy(scratch, output, static_cast<unsigned>(count) * sizeof(scratch[0]));
        }
    }
}

} // namespace rage
