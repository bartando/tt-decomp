#pragma once
#include "rage/ptr32.hpp"
#include <cstdint>

extern "C" {
void grc_2CC8(void* resource, uint32_t data, uint32_t auxiliary); // @ 0x82352CC8
uint32_t grcResource_ReleaseRef(void* resource); // @ 0x82352EE0
extern rage::ptr32<void> g_grcSharedSurfacePair[2]; // @ 0x825EBA08
extern rage::ptr32<void> g_grcSharedSurface; // @ 0x825EB984
extern rage::ptr32<void> g_grcSharedTexture; // @ 0x825EB9E0
}
void grcDevice_cleanupInternal(void* holder); // @ 0x82151068
void grcDevice_releaseSharedResources(); // @ 0x8214F338
