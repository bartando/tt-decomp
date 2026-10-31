// Pad axis decoding and dead-zone remapping, recovered from the PPC.
#include <cstdint>

extern "C" int pongPlayer_0270_g(const void*, int); // @ 0x821E0270

// Each button has four history bytes. XOR with byte 3 undoes its polarity.
// @ 0x821E00D8 | size: 0x60
float pongPad_DecodeAxis(const void* button) {
    const auto* bytes = static_cast<const uint8_t*>(button);
    const float centered = float(bytes[3] ^ bytes[0]) - 127.5f;
    const float value = centered * 0.007843137718737125f;
    if (value < -1.0f) return -1.0f;
    if (value > 1.0f) return 1.0f;
    return value;
}

// f1 on entry is unused. The result is returned in f1, not through r5.
// @ 0x821E0508 | size: 0x9C
float pongPlayer_0508_g(void* pad, int channel) {
    const int index = pongPlayer_0270_g(pad, channel);
    const auto* buttons = *reinterpret_cast<const uint8_t* const*>(
        static_cast<const uint8_t*>(pad) + 0x31C);
    const float value = pongPad_DecodeAxis(buttons + index * 4);
    if (value > 0.25999999046325684f)
        return (value - 0.25999999046325684f) * 1.3513513803482056f;
    if (value < -0.25999999046325684f)
        return (value + 0.25999999046325684f) * 1.3513513803482056f;
    return 0.0f;
}
