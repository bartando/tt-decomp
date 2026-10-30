#include <cstdint>

namespace rage {

struct XactFade {
    void** vtable;
    float value;
    uint16_t duration;
    uint16_t reserved;
    uint32_t curve;
    uint32_t state;
    float progress;
};

extern const float g_xactFadeZero; // @ 0x82003DA8
extern const float g_xactFadeOne;  // @ 0x82003DAC
extern const float g_xactFadeStep; // @ 0x82004AA8
extern void xactFade_ApplyCurve(XactFade* fade); // @ 0x82453A98

// @ 0x82453B48
// Formerly msgMsgSink_3B48_g. State 1 fades down, state 2 fades up.
int32_t xactFade_Update(XactFade* fade) {
    if (fade->state != 1 && fade->state != 2) return 0;

    const float step = g_xactFadeStep / static_cast<float>(fade->duration);
    if (fade->state == 2) {
        fade->progress += step;
        if (!(fade->progress >= g_xactFadeOne)) {
            xactFade_ApplyCurve(fade);
        } else {
            fade->value = g_xactFadeOne;
            fade->state = 0;
            using Callback = void (*)(XactFade*);
            reinterpret_cast<Callback>(fade->vtable[1])(fade);
        }
    } else {
        fade->progress -= step;
        if (!(fade->progress <= g_xactFadeZero)) {
            xactFade_ApplyCurve(fade);
        } else {
            fade->value = g_xactFadeZero;
            fade->state = 0;
            using Callback = void (*)(XactFade*);
            reinterpret_cast<Callback>(fade->vtable[0])(fade);
        }
    }
    return 1;
}

}
