#include "rage/dat_bit_buffer.hpp"
#include <cstdint>

// @ 0x82390608 | size: 0x13C
// Score payload: signed index, three unsigned bytes, four flags, signed byte,
// and a float. The stream is the second argument, as at 0x823BD804.
void netScore_Deserialise(void* score, void* client) {
    auto* bytes = static_cast<uint8_t*>(score);
    datBitBuffer_ReadU8(client, bytes + 4, 8);
    datBitBuffer_ReadU8(client, bytes + 5, 8);
    datBitBuffer_ReadU8(client, bytes + 6, 8);
    datBitBuffer_ReadS32(client, reinterpret_cast<int32_t*>(bytes), 32);
    uint32_t temporary;
    for (int offset = 7; offset <= 10; ++offset) {
        datBitBuffer_ReadU32(client, &temporary, 1);
        bytes[offset] = temporary != 0;
    }
    datBitBuffer_ReadS8(client, reinterpret_cast<int8_t*>(bytes + 11));
    datBitBuffer_ReadU32(client, &temporary, 32);
    __builtin_memcpy(bytes + 12, &temporary, 4);
}
