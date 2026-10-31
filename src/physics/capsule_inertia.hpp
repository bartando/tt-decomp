#pragma once

namespace rage {
// A diagonal inertia vector returned through Xenon's hidden result pointer.
struct phInertiaDiagonal {
    float xyz[3];
};
}

// r3-r5 are unused; the original consumes mass/radius/length in f1-f3 and
// writes its three results through r6. Keep this ABI for direct PPC callers.
void phCapsule_ComputeInertia(void* unused3, const void* unused4, void* unused5,
                             float* output, float mass, float radius, float length);
