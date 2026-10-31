#pragma once
#include <cstdint>

void swfSelectPageGroup(void* group, uint32_t bindGlobals); // @ 0x823F9040
extern "C" void* swfFindPageGroupValue(void* group, const char* key); // @ 0x823F9280
extern "C" void* swfGetOrCreatePageGroupValue(void* group, const char* key); // @ 0x823F9318
// A missing value leaves *output unchanged.
bool swfGetPageGroupInteger(void* group, const char* key, int32_t* output); // @ 0x823F9808
