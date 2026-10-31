#include "ball_predict.hpp"

extern "C" const float g_floatConstant4; // @ 0x825C7600

// @ 0x821D5128 | size: 0xA0
// Partial shot initialization: padding, unused vectors and their w lanes stay
// untouched. This is distinct from the full-vector reset at 0x821D51C8.
void ballPredict_InitialiseShot(bpShot* shot) {
    shot->f00[0] = 1.0f;
    shot->f00[1] = 0.0f;
    shot->f00[2] = 0.0f;
    shot->v30[0] = {};
    shot->v50.x = shot->v50.y = shot->v50.z = 0.0f;
    shot->v60.x = shot->v60.y = shot->v60.z = 0.0f;
    shot->i88 = 1;
    shot->i8C = 0;
    shot->f70[0] = 0.0f;
    shot->f70[1] = 0.0f;
    shot->f70[3] = 1.0f;
    shot->f70[4] = 0.0f;
    shot->f70[5] = g_floatConstant4;
    shot->v90.x = shot->v90.y = shot->v90.z = 0.0f;
    shot->vA0.x = shot->vA0.y = shot->vA0.z = 0.0f;
    shot->hB0 = 0;
    shot->hB2 = 0xFFFF;
    shot->bB4 = 0;
    shot->hB6 = 0;
}
