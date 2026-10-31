#pragma once
#include <cstdint>
#include "rage/swf_value.hpp"

// Native dispatch binding for executable code, outside game object layouts.
using SwfCommandHandler = void (*)(const char*, const SwfVmValue*);
extern "C" SwfCommandHandler g_swfCommandHandler; // @ 0x826066D4
void hudFlashBase_ScriptCommand(const char* command, const SwfVmValue* argument); // @ 0x822EC418

void swfSelectPageGroup(void* group, uint32_t bindGlobals); // @ 0x823F9040
extern "C" void* swfFindPageGroupValue(void* group, const char* key); // @ 0x823F9280
extern "C" void* swfGetOrCreatePageGroupValue(void* group, const char* key); // @ 0x823F9318
// A missing value leaves *output unchanged.
bool swfGetPageGroupInteger(void* group, const char* key, int32_t* output); // @ 0x823F9808
