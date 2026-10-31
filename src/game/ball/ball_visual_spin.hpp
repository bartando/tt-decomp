#pragma once
struct gmBallNode;

// Matrix is four aligned, four-float rows. Position occupies an unused ABI home.
void BallNode_IntegrateVisualSpin(gmBallNode* node,const float* unusedPosition,
                                 const float* spin,float* matrix,float dt); // @ 0x82282240
