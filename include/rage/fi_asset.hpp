#pragma once
#include <cstdint>

extern "C" void fiAssetManager_PushFolder(void* assets, const char* path); // @ 0x822E2E60
extern "C" void fiPath_Build(void* assets, char* destination, int32_t capacity,
                              const char* name, const char* extension, int32_t root); // @ 0x822E2B50
