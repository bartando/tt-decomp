// Apply the visual spin increment, then rebuild the ball's matrix basis.
#include "ball_visual_spin.hpp"
#include "pong_ball.hpp"
#include "rage/mat33.hpp"
#include <cstdint>
#include <cmath>
#pragma clang fp contract(off)

extern double crt_sqrt(double value); // @ 0x824301D0
extern "C" const float lbl_825CB7C0[4]; // @ 0x825CB7C0

namespace {
float FlushSpin(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits,&value,4);
    if ((bits&0x7F800000u)==0) bits&=0x80000000u;
    __builtin_memcpy(&value,&bits,4);
    return value;
}
}

// @ 0x82282240
void BallNode_IntegrateVisualSpin(gmBallNode* node,const float* /*unusedPosition*/,
                                 const float* spin,float* matrix,float dt) {
    const float scale=node->visualSpinScale*dt;
    alignas(16) float increment[4];
    for(int lane=0;lane<4;++lane) increment[lane]=FlushSpin(FlushSpin(spin[lane])*FlushSpin(scale));
    const double x=increment[0],y=increment[1],z=increment[2];
    const float square=FlushSpin(static_cast<float>((x*x+y*y)+z*z));
    if (!(square>0x1p-126f)) return;
    const float angle=static_cast<float>(crt_sqrt(square));
    const float reciprocal=FlushSpin(1.0f/angle);
    alignas(16) float axis[4];
    for(int lane=0;lane<4;++lane) {
        const float error=-FlushSpin(FlushSpin(reciprocal*FlushSpin(angle))-FlushSpin(lbl_825CB7C0[lane]));
        const float inverse=FlushSpin(FlushSpin(reciprocal*error)+reciprocal);
        axis[lane]=FlushSpin(increment[lane]*inverse);
    }
    alignas(16) float rotation[16];
    rage::mat33RotationNormalizedAxis(rotation,axis,angle);
    rage::mat33ComposeInPlace(matrix,rotation);
    rage::mat33Orthonormalize(matrix);
}
