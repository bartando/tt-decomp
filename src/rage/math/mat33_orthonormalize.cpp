// Rebuild a right-handed orthonormal basis while retaining the third axis.
#include "rage/mat33.hpp"
#include <cstdint>
#include <cmath>
#pragma clang fp contract(off)

extern "C" const float lbl_82619BF0[4]; // @ 0x82619BF0
extern "C" const float lbl_82606750[4]; // @ 0x82606750
extern "C" const float lbl_825CB7C0[4]; // @ 0x825CB7C0
extern "C" const float lbl_825CB7D0[4]; // @ 0x825CB7D0

namespace rage {
namespace {
float FlushBasis(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits,&value,4);
    if ((bits & 0x7F800000u) == 0) bits &= 0x80000000u;
    __builtin_memcpy(&value,&bits,4);
    return value;
}

void CrossBasis(float* out,const float* a,const float* b) {
    for (int lane=0;lane<4;++lane) {
        const int first=lane<3 ? (lane+1)%3 : 3;
        const int second=lane<3 ? (lane+2)%3 : 3;
        const float positive=FlushBasis(FlushBasis(a[first])*FlushBasis(b[second]));
        const float negative=FlushBasis(FlushBasis(a[second])*FlushBasis(b[first]));
        out[lane]=-FlushBasis(negative-positive);
    }
}

void NormalizeBasis(float* vector) {
    const double x=FlushBasis(vector[0]),y=FlushBasis(vector[1]),z=FlushBasis(vector[2]);
    const float square=FlushBasis(static_cast<float>((x*x+y*y)+z*z));
    const float estimate=FlushBasis(static_cast<float>(1.0/__builtin_sqrt(static_cast<double>(square))));
    for(int lane=0;lane<4;++lane) {
        const float inverse=estimate==FlushBasis(lbl_82619BF0[lane]) ? lbl_82606750[lane] : estimate;
        const float squared=FlushBasis(FlushBasis(inverse)*FlushBasis(inverse));
        const float half=FlushBasis(FlushBasis(lbl_825CB7D0[lane])*FlushBasis(inverse));
        const float error=-FlushBasis(FlushBasis(square*squared)-FlushBasis(lbl_825CB7C0[lane]));
        const float refined=FlushBasis(FlushBasis(error*half)+FlushBasis(inverse));
        vector[lane]=FlushBasis(FlushBasis(vector[lane])*refined);
    }
}
}

// @ 0x820C9220
void mat33Orthonormalize(float* matrix) {
    alignas(16) float first[4],second[4],third[4];
    __builtin_memcpy(second,matrix+4,16);
    __builtin_memcpy(third,matrix+8,16);
    CrossBasis(first,second,third);
    NormalizeBasis(first);
    __builtin_memcpy(matrix,first,16);
    CrossBasis(second,third,first);
    NormalizeBasis(second);
    __builtin_memcpy(matrix+4,second,16);
    NormalizeBasis(third);
    __builtin_memcpy(matrix+8,third,16);
}
} // namespace rage
