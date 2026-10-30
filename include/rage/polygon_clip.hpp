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

} // namespace rage
