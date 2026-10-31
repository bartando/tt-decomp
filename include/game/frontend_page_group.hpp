#pragma once
#include <cstdint>
#include "rage/ptr32.hpp"

void CreditsPageGroup_PollInput(void* group); // @ 0x82320890
void* CreditsPageGroup_Construct(void* memory); // @ 0x8231F4C0
void* LegalsPageGroup_Construct(void* memory); // @ 0x82309358
void LegalsPageGroup_Register(void* group); // @ 0x82309510
void* DialogPageGroup_Construct(void* memory); // @ 0x82321620
uint32_t DialogPageGroup_IsComplete(void* group); // @ 0x82322470
extern "C" uint32_t g_creditsResourceVersion; // @ 0x82606520
extern "C" uint32_t g_dialogResourceVersion; // @ 0x82606514
extern "C" uint32_t g_legalsResourceVersion; // @ 0x8260652C
extern "C" rage::ptr32<void> g_dialogPageGroup; // @ 0x82606628
