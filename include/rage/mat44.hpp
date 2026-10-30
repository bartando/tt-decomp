#pragma once

namespace rage {
// Compose an aligned affine transform in place. The original packs each input
// row's x into output w; translation is made homogeneous before source loads.
void mat44ComposeAffineInPlace(void* matrix, const void* transform); // @ 0x820C3AD8
}
