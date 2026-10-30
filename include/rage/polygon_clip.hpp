#pragma once

#include <cstdint>

namespace rage {

// VMX loads/stores use aligned, 16-byte vertices, including the fourth lane.
// Output must be separate from input, with space for up to 2 * vertexCount vertices.
// r3 is unused in the original; retain it so the remaining arguments occupy r4..r8.
void clipPolygonToPlane(void* context, int32_t vertexCount, const float (*vertices)[4],
                        int32_t* outputCount, float (*output)[4], const float* plane);

} // namespace rage
