#pragma once

void phArticulatedCollider_ApplyPointImpulseResponse(void* jointData, int bodyIndex,
                                                    const float* force, const float* point); // @ 0x822571C8
void phArticulatedCollider_ApplyAngularImpulseResponse(void* jointData, int bodyIndex,
                                                      const float* torque); // @ 0x82257368
void phArticulatedCollider_BuildPointResponse(void* jointData, int bodyIndex,
                                             const float* point); // @ 0x822577F0
void phArticulatedCollider_BuildAngularResponse(void* jointData, int bodyIndex); // @ 0x82257918
void phArticulatedCollider_GetPointResponseMatrix(void* jointData, int bodyIndex,
                                                 const float* point, float* output); // @ 0x82257A30
