#pragma once

#include <cstdint>

namespace rage {

// VMX loads/stores use aligned, 16-byte vertices, including the fourth lane.
// Output must be separate from input, with space for up to 2 * vertexCount vertices.
// r3 is unused in the original; retain it so the remaining arguments occupy r4..r8.
void clipPolygonToPlane(void* context, int32_t vertexCount, const float (*vertices)[4],
                        int32_t* outputCount, float (*output)[4], const float* plane);

// Clip two aligned vertices against one plane. Input and output must be disjoint.
// vertexCount is copied to outputCount unless both vertices are outside.
void clipLineToPlane(void* context, int32_t vertexCount, const float (*vertices)[4],
                     int32_t* outputCount, float (*output)[4], const float* plane);

// Clips four input vertices against six planes; referencePoint may skip planes.
// The output must be disjoint from the input and have room for the clipped polygon.
// If every plane is skipped, outputCount and output are left untouched.
void clipPolygonToFrustum(void* context, int32_t unusedCount, const float (*vertices)[4],
                          int32_t* outputCount, float (*output)[4], const float (*planes)[4],
                          const float* referencePoint);

// Clip two vertices successively against six planes; referencePoint may skip planes.
void clipLineToFrustum(void* context, int32_t unusedCount, const float (*vertices)[4],
                       int32_t* outputCount, float (*output)[4], const float (*planes)[4],
                       const float* referencePoint);

// Intersect a world AABB with a camera frustum, then rebuild its world-space AABB.
// box has three aligned vec4s: center, full size, and auxiliary data. Rejection clears
// all three; an initially zero size returns false without writing. Success changes
// center/size xyz only (the original's two w results are indeterminate stack padding).
// cameraToWorld is an aligned affine matrix; referencePoint is optional, in camera space.
// Preserve LTCG's unused r6..r9 slots so referencePoint occupies its original r10.
bool clipAabbToFrustum(void* context, float (*box)[4], const float (*cameraToWorld)[4],
                       uint32_t r6, uint32_t r7, uint32_t r8, uint32_t r9,
                       const float* referencePoint, float nearClip, float farClip, float fov, float aspect);

} // namespace rage
