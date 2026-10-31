#pragma once

#include <cstdint>

// The interpreter's tagged eight-byte value. Pointer payloads are loaded with
// load_ptr32; integer and float payloads use the same four bytes.
struct SwfVmValue {
    uint32_t payload;
    uint32_t tag;
};
static_assert(sizeof(SwfVmValue) == 8);

extern "C" {
uint8_t swfValueIsInteger(const SwfVmValue* value); // @ 0x823FA4C8
uint8_t swfValuesEqual(const SwfVmValue* a, const SwfVmValue* b); // @ 0x823FA928
}
