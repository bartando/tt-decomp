/**
 * button_edges.cpp — has a button just been pressed
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 */

#include <cstdint>

// @ 0x821DFFF8 — pg_FFF8_g. A button's record keeps this frame's state byte
// at +0, last frame's at +1 and the released state at +3; bit 7 is the
// button. True when it differs from released now but didn't last frame.
bool CheckButtonPressed(void* record) {
    const uint8_t* b = static_cast<const uint8_t*>(record);
    if (((b[0] ^ b[3]) & 0xFF) <= 0x7F) {
        return false;
    }
    return ((b[1] ^ b[3]) & 0xFF) <= 0x7F;
}
