#include <cstdint>

// @ 0x82483348 | size: 0x8
void set_3348(void* object, float value) {
    *reinterpret_cast<float*>(static_cast<uint8_t*>(object) + 0x48) = value;
}
