#pragma once

namespace rage {
void phBoundComposite_RebuildExtents(void* bound); // @ 0x8228E888
float phBoundComposite_ComputeRadius(void* bound, const float* partMatrices,
                                     const float* centroid); // @ 0x8228ECB0
}
