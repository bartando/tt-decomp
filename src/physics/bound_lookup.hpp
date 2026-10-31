#pragma once
#include <stdint.h>

namespace rage {
struct phArticulatedCollider;
uint32_t phBoundComposite_E750(void* bound); // @ 0x8228E750
int32_t phBoundComposite_ResolveBoundIndex(void* bound, int32_t index); // @ 0x8228F5C8
}

int phArticulatedCollider_E668(rage::phArticulatedCollider* collider, int boneIndex); // @ 0x8224E668
