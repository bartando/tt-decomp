#pragma once
#include <stdint.h>

// One row for each scalar joint limit; return the number of rows written.
int32_t phArticulatedCollider_GatherJointLimits(void* jointData, uint32_t* jointIndices,
    uint32_t* states, float* errors, float* referenceErrors, float* weights); // @ 0x82258C98
