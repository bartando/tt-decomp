/**
 * dat_parser_fields.cpp — registering a tunable field with a datParser
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Classes with tunables describe each field to a parser (type, name, where
 * it lives). The symbol map files the function under pongHairData, the first
 * class it was found in; callers declare it under that name.
 */

#include <cstdint>

extern "C" void* xe_EC88(uint32_t size);                   // @ 0x820DEC88 — operator new
extern "C" void* const datParserRecord_vtable[];           // @ 0x82037494

namespace {

struct datParserFieldRecord {
    void* const*          m_pVtable;   // +0x00
    int32_t               m_type;      // +0x04
    uint16_t              m_flags;     // +0x08
    uint8_t               m_pad0A[2];
    char                  m_name[64];  // +0x0C
    void*                 m_pField;    // +0x4C
    uint32_t              m_field50;   // +0x50
    datParserFieldRecord* m_pNext;     // +0x54
};

struct datParserView {
    uint8_t               m_pad00[0x44];
    int32_t               m_fieldCount;          // +0x44
    uint8_t               m_pad48[0x04];
    datParserFieldRecord* m_pFirstField;         // +0x4C
    uint8_t               m_pad50[0x04];
    datParserFieldRecord  m_fieldPool[64];       // +0x54
    int32_t               m_fieldPoolUsed;       // +0x1654
};

}  // namespace

// @ 0x82177B60 — datParser::AddField (pongHairData_7B60_g)
// Takes a record from the parser's pool of 64 (pool records are reused as
// they are), or a new one once the pool is gone, fills it in and appends it
// to the parser's field list. The name is copied without its spaces, at most
// 63 characters. Callers pass up to three more arguments; it reads none of them.
void* datParser_AddField(void* parserp, int32_t type, const char* name, void* field) {
    datParserView* parser = static_cast<datParserView*>(parserp);

    datParserFieldRecord* rec;
    if (parser->m_fieldPoolUsed < 64) {
        rec = &parser->m_fieldPool[parser->m_fieldPoolUsed++];
    } else {
        rec = static_cast<datParserFieldRecord*>(xe_EC88(sizeof(datParserFieldRecord)));
        if (rec != nullptr) {
            rec->m_type = 0;
            rec->m_name[0] = '\0';
            rec->m_pField = nullptr;
            rec->m_field50 = 0;
            rec->m_pNext = nullptr;
            rec->m_pVtable = datParserRecord_vtable;
        }
    }

    int32_t len = 0;
    do {
        const char c = *name++;
        if (c == '\0') {
            break;
        }
        if (c != ' ') {
            rec->m_name[len++] = c;
        }
    } while (len < 63);
    rec->m_name[len] = '\0';
    rec->m_pField = field;
    rec->m_type = type;
    rec->m_flags = 1;
    rec->m_field50 = 0;

    if (parser->m_pFirstField == nullptr) {
        parser->m_pFirstField = rec;
    } else {
        datParserFieldRecord* last = parser->m_pFirstField;
        while (last->m_pNext != nullptr) {
            last = last->m_pNext;
        }
        last->m_pNext = rec;
    }
    parser->m_fieldCount++;
    return rec;
}

// char_view.cpp and pong_camera.cpp declare it extern "C" as pongHairData_7B60_g.
extern "C" void* pongHairData_7B60_g(void* parser, int32_t type, const char* name, void* field) {
    return datParser_AddField(parser, type, name, field);
}

// pong_camera.cpp's camViewCS::RegisterParams calls it under this name.
void pongCameraView_RegisterParamHook(void* parser, int type, const char* name, void* field, int, int) {
    datParser_AddField(parser, type, name, field);
}

// rage_audio.cpp names it with __asm__("pongHairData_7B60_g"), which on Mach-O
// is the symbol without the leading underscore C names get. On ELF that is the
// C name above already.
#if defined(__APPLE__)
__asm__(".globl pongHairData_7B60_g\n.set pongHairData_7B60_g, _pongHairData_7B60_g");
#endif
