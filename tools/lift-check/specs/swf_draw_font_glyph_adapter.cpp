#define swfDrawFontGlyph liftcheck_glyph_impl
#include "../../../src/rage/swf.cpp"

// Xenon float arguments consume GPR slots; PPC32 floats do not. Preserve the
// atlas in r3 and f1..f3, moving the glyph index from Xenon r7 to PPC32 r4.
extern "C" __attribute__((naked)) void liftcheck_glyph_adapter() {
    __asm__ volatile(
        "mr 4, 7\n"
        "b _ZN4rage20liftcheck_glyph_implEPKNS_12swfFontAtlasEfffi\n");
}
