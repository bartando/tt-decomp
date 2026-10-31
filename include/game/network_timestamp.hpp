#pragma once
#include <cstdint>

// Retail ignores the supplied bound and always writes with capacity 50.
int networkFormatElapsedTime(char* destination, uint32_t unusedCapacity, float seconds); // @ 0x8239BE30
const char* networkClockTimestamp(void* clock, int slot); // @ 0x82391480
char* FormatTimestampForLog(void* timestamp); // @ 0x8239BF30
