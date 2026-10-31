// Affine point transform used by ball trail placement.
#include "rage/mat44.hpp"
#include <cstdint>
#pragma clang fp contract(off)

extern "C" const uint32_t g_affineXYZMask[4]; // @ 0x82619BE0
extern "C" const uint32_t g_affineHomogeneousW[4]; // @ 0x82619BD0

namespace rage {
namespace {
float FlushPoint(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits,&value,4);
    if ((bits&0x7F800000u)==0) bits&=0x80000000u;
    __builtin_memcpy(&value,&bits,4);
    return value;
}
}

// All source lanes are loaded before writing, including when point aliases matrix.
// The final vector merge retains the homogeneous input X in the fourth lane.
// @ 0x820D2038
void mat34TransformPointInPlace(const float* matrix,float* point) {
    float rows[16],homogeneous[4],result[4];
    __builtin_memcpy(rows,matrix,64);
    for(int lane=0;lane<4;++lane) {
        uint32_t bits;
        __builtin_memcpy(&bits,point+lane,4);
        bits=(bits&g_affineXYZMask[lane])|g_affineHomogeneousW[lane];
        __builtin_memcpy(homogeneous+lane,&bits,4);
    }
    for(int axis=0;axis<3;++axis) {
        double sum=0.0;
        for(int row=0;row<4;++row)
            sum+=static_cast<double>(FlushPoint(homogeneous[row]))*FlushPoint(rows[row*4+axis]);
        result[axis]=FlushPoint(static_cast<float>(sum));
    }
    __builtin_memcpy(result+3,homogeneous,4);
    __builtin_memcpy(point,result,16);
}
} // namespace rage
