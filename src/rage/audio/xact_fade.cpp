#include "audio/xact_fade.hpp"
#include <cmath>

namespace rage {


extern const float g_xactFadeZero; // @ 0x82003DA8
extern const float g_xactFadeOne;  // @ 0x82003DAC
extern const float g_xactFadeStep; // @ 0x82004AA8
extern const double g_xactFadeHalfPi; // @ 0x82004AA0
extern const double g_xactFadeLogBase; // @ 0x82079B68
extern const float g_xactFadeLogScale; // @ 0x82004A9C

// @ 0x82453A98
void xactFade_ApplyCurve(XactFade* fade) {
    switch (fade->curve) {
    case 1: {
        // Retail rounds pow's result to float before multiplying by 0.1f.
        const float power = static_cast<float>(std::pow(g_xactFadeLogBase, static_cast<double>(fade->progress)));
        fade->value = power * g_xactFadeLogScale;
        break;
    }
    case 2:
        fade->value = static_cast<float>(std::sin(static_cast<double>(fade->progress) * g_xactFadeHalfPi));
        break;
    default:
        fade->value = fade->progress;
        break;
    }
}

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
            fade->FadeInComplete();
        }
    } else {
        fade->progress -= step;
        if (!(fade->progress <= g_xactFadeZero)) {
            xactFade_ApplyCurve(fade);
        } else {
            fade->value = g_xactFadeZero;
            fade->state = 0;
            fade->FadeOutComplete();
        }
    }
    return 1;
}

}
