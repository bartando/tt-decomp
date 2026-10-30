// Narrow MSVC CRT printf engine (_output_l family), not fiAsciiTokenizer.
// sprintf wrapper @ 0x82430030 and vsnprintf wrapper @ 0x82432878 construct string FILEs
// and call this entry. The locale argument is unused on this Xenon CRT.
#include <cstdint>
#include <cstddef>

struct CrtFile {
    unsigned char* cursor;
    int remaining;
    unsigned char* base;
    unsigned flags;
    int descriptor;
    unsigned char reserved[12];
};

struct CrtIoEntry {
    unsigned char reserved[40];
    unsigned char textMode;
    unsigned char tail[3];
};

struct CrtCountedString {
    int16_t length;
    uint16_t capacity;
    unsigned char* data;
};

struct CrtPrintLocale { unsigned char reserved[24]; };
struct CrtFloatFormatters {
    void* reserved[6];
    void (*format)(const uint64_t*, unsigned char*, int, int, int, int, CrtPrintLocale*);
    void* reserved28;
    void (*cropZeros)(unsigned char*, CrtPrintLocale*);
    void (*forceDecimal)(unsigned char*, CrtPrintLocale*);
};

extern "C" {
    int* crtErrno(); // @ 0x824355A8
    void crtInvalidParameter(void*, void*, void*, unsigned, uintptr_t); // @ 0x82435458
    int crtFileDescriptor(CrtFile*); // @ 0x824367A0
    unsigned char* crtStandardStreams(); // @ 0x82433438
    void crtWriteChar(int, CrtFile*, int*); // @ 0x824347A0
    int crtFlushChar(int, CrtFile*); // @ 0x824345C8
    void crtWriteBlock(const void*, int, CrtFile*, int*); // @ 0x82434838
    int crtIsLeadByte(int, CrtPrintLocale*); // @ 0x8243A348
    int crtWideCharToMultibyte(int*, unsigned char*, int, unsigned); // @ 0x8243A340
    int crtCountOutputEnabled(); // @ 0x8243A1F8
    void* crtMalloc(unsigned); // @ 0x82433370
    void crtFree(void*); // @ 0x82433310
    int crtVsnprintf(unsigned char*, unsigned, const char*, const unsigned char*); // @ 0x82432958
    void crtDebugString(const unsigned char*); // @ 0x825680B0

    extern CrtIoEntry* crtIoBlocks[]; // @ 0x82732F40
    extern CrtIoEntry crtBadIoEntry; // @ 0x825B13C4
    extern const unsigned char crtPrintfStates[]; // @ 0x82001D98
    extern const unsigned char* crtNullString; // @ 0x82001D8C
    extern const uint16_t* crtNullWideString; // @ 0x82001D90
    extern CrtPrintLocale crtPrintLocale; // @ 0x825B14D8
    extern CrtFloatFormatters crtFloatFormatters; // @ 0x825B14F0
}

namespace {
enum PrintFlags : unsigned {
    Plus = 1, Space = 2, Left = 4, Zero = 8, Long = 16, Short = 32,
    Signed = 64, Alternate = 128, Negative = 256, Octal = 512,
    Wide = 2048, LongLong = 4096, Int64 = 32768
};

// Xenon va_list slots are eight-byte aligned. Scalars/pointers occupy the
// low word (slot + 4) in big-endian memory; 64-bit integers/doubles use it all.
const unsigned char* nextPrintArg(const unsigned char*& args) {
    const uintptr_t aligned = (reinterpret_cast<uintptr_t>(args) + 7) & ~uintptr_t(7);
    args = reinterpret_cast<const unsigned char*>(aligned + 8);
    return reinterpret_cast<const unsigned char*>(aligned);
}

uint32_t printWord(const unsigned char*& args) {
    return *reinterpret_cast<const uint32_t*>(nextPrintArg(args) + 4);
}

int invalidPrintArgument() {
    *crtErrno() = 22;
    crtInvalidParameter(nullptr, nullptr, nullptr, 0, 0);
    return -1;
}

CrtIoEntry* printIoEntry(CrtFile* stream) {
    if (crtFileDescriptor(stream) == -1 || crtFileDescriptor(stream) == -2)
        return &crtBadIoEntry;
    const int block = crtFileDescriptor(stream) >> 5;
    const unsigned index = static_cast<unsigned>(crtFileDescriptor(stream)) & 31;
    return &crtIoBlocks[block][index];
}
} // namespace

// @ 0x824347A0 | size: 0x94
extern "C" void crtWriteChar(int ch, CrtFile* stream, int* count) {
    if (!(stream->flags & 0x40) || stream->base) {
        const uint32_t remaining = static_cast<uint32_t>(stream->remaining) - 1;
        stream->remaining = static_cast<int32_t>(remaining);
        int result;
        if (!(remaining & 0x80000000u)) {
            *stream->cursor++ = static_cast<unsigned char>(ch);
            result = static_cast<unsigned char>(ch);
        } else {
            result = crtFlushChar(static_cast<int8_t>(ch), stream);
        }
        if (result == -1) {
            *count = -1;
            return;
        }
    }
    *count = static_cast<int32_t>(static_cast<uint32_t>(*count) + 1);
}

// @ 0x824348D0 | size: 0xB84
extern "C" int crtOutput(CrtFile* stream, const char* format, void* /*locale*/,
                         const unsigned char* args) {
    if (!stream)
        return invalidPrintArgument();
    if (!(stream->flags & 0x40)) {
        if ((printIoEntry(stream)->textMode & 0xFE) != 0)
            return invalidPrintArgument();
        if ((printIoEntry(stream)->textMode & 1) != 0)
            return invalidPrintArgument();
    }
    if (!format)
        return invalidPrintArgument();

    if (reinterpret_cast<unsigned char*>(stream) == crtStandardStreams() + 32 ||
        reinterpret_cast<unsigned char*>(stream) == crtStandardStreams() + 64) {
        unsigned char debug[512];
        int result = crtVsnprintf(debug, 512, format, args);
        if (result == -1) {
            result = 511;
            debug[511] = 0;
        }
        crtDebugString(debug);
        return result;
    }

    int count = 0, state = 0, width = 0, precision = 0, length = 0;
    int prefixLength = 0, hexOffset = 0, capital = 0;
    unsigned flags = 0;
    bool wide = false, suppress = false;
    unsigned char prefix[2];
    unsigned char buffer[512];
    const unsigned char* text = nullptr;
    void* allocated = nullptr;

    for (unsigned char ch = static_cast<unsigned char>(*format); ch;
         ch = static_cast<unsigned char>(*format)) {
        ++format;
        if (count < 0)
            break;
        int category = ch >= 32 && ch <= 120 ? crtPrintfStates[ch - 32] & 15 : 0;
        state = static_cast<int8_t>(crtPrintfStates[category * 8 + state]) >> 4;
        switch (state) {
        case 1:
            flags = 0;
            precision = -1;
            capital = 0;
            wide = false;
            suppress = false;
            width = prefixLength = 0;
            break;
        case 2:
            switch (ch) {
            case ' ': flags |= Space; break;
            case '#': flags |= Alternate; break;
            case '+': flags |= Plus; break;
            case '-': flags |= Left; break;
            case '0': flags |= Zero; break;
            }
            break;
        case 3:
            if (ch == '*') {
                width = static_cast<int32_t>(printWord(args));
                if (width < 0) {
                    flags |= Left;
                    width = static_cast<int>(0u - static_cast<unsigned>(width));
                }
            } else {
                width = static_cast<int>(static_cast<unsigned>(width) * 10 + ch - '0');
            }
            break;
        case 4: precision = 0; break;
        case 5:
            if (ch == '*') {
                precision = static_cast<int32_t>(printWord(args));
                if (precision < 0) precision = -1;
            } else {
                precision = static_cast<int>(static_cast<unsigned>(precision) * 10 + ch - '0');
            }
            break;
        case 6:
            switch (ch) {
            case 'h': flags |= Short; break;
            case 'w': flags |= Wide; break;
            case 'l':
                if (*format == 'l') { ++format; flags |= LongLong; }
                else flags |= Long;
                break;
            case 'I':
                if (format[0] == '6' && format[1] == '4') { format += 2; flags |= Int64; }
                else if (format[0] == '3' && format[1] == '2') { format += 2; flags &= ~Int64; }
                else if (*format != 'd' && *format != 'i' && *format != 'o' &&
                         *format != 'u' && *format != 'x' && *format != 'X') {
                    state = 0;
                    wide = false;
                    if (crtIsLeadByte(ch, &crtPrintLocale)) {
                        crtWriteChar(ch, stream, &count);
                        ch = static_cast<unsigned char>(*format++);
                        if (!ch) return invalidPrintArgument();
                    }
                    crtWriteChar(ch, stream, &count);
                }
                break;
            }
            break;
        case 0:
            wide = false;
            if (crtIsLeadByte(ch, &crtPrintLocale)) {
                crtWriteChar(ch, stream, &count);
                ch = static_cast<unsigned char>(*format++);
                if (!ch) return invalidPrintArgument();
            }
            crtWriteChar(ch, stream, &count);
            break;
        case 7: {
            bool integer = false;
            unsigned radix = 10;
            switch (ch) {
            case 'C':
                if (!(flags & (Wide | Long | Short))) flags |= Wide;
                [[fallthrough]];
            case 'c': {
                const uint32_t value = printWord(args);
                if (flags & (Wide | Long)) {
                    if (crtWideCharToMultibyte(&length, buffer, 512, value & 0xFFFF) != 0)
                        suppress = true;
                } else {
                    buffer[0] = static_cast<unsigned char>(value);
                    length = 1;
                }
                text = buffer;
                break;
            }
            case 'Z': {
                const auto* value = reinterpret_cast<const CrtCountedString*>(uintptr_t(printWord(args)));
                if (value && value->data) {
                    text = value->data;
                    wide = (flags & Wide) != 0;
                    length = wide ? value->length / 2 : value->length;
                } else {
                    text = crtNullString;
                    length = 0;
                    while (text[length]) ++length;
                }
                break;
            }
            case 'S':
                if (!(flags & (Wide | Long | Short))) flags |= Wide;
                [[fallthrough]];
            case 's': {
                int limit = precision == -1 ? 0x7FFFFFFF : precision;
                text = reinterpret_cast<const unsigned char*>(uintptr_t(printWord(args)));
                if (flags & (Wide | Long)) {
                    if (!text) text = reinterpret_cast<const unsigned char*>(crtNullWideString);
                    wide = true;
                    const auto* p = reinterpret_cast<const uint16_t*>(text);
                    length = 0;
                    while (limit-- != 0 && p[length]) ++length;
                } else {
                    if (!text) text = crtNullString;
                    length = 0;
                    while (limit-- != 0 && text[length]) ++length;
                }
                break;
            }
            case 'n': {
                void* destination = reinterpret_cast<void*>(uintptr_t(printWord(args)));
                if (!crtCountOutputEnabled()) return invalidPrintArgument();
                if (flags & Short) *static_cast<int16_t*>(destination) = static_cast<int16_t>(count);
                else *static_cast<int*>(destination) = count;
                suppress = true;
                break;
            }
            case 'A': case 'E': case 'G':
                ch += 32;
                capital = 1;
                [[fallthrough]];
            case 'a': case 'e': case 'f': case 'g': {
                flags |= Signed;
                unsigned char* output = buffer;
                int capacity = 512;
                if (precision < 0) precision = 6;
                else if (precision == 0) { if (ch == 'g') precision = 1; }
                else {
                    if (precision > 512) precision = 512;
                    if (precision > 163) {
                        capacity = precision + 349;
                        allocated = crtMalloc(capacity);
                        if (allocated) output = static_cast<unsigned char*>(allocated);
                        else { precision = 163; capacity = 512; }
                    }
                }
                const uint64_t value = *reinterpret_cast<const uint64_t*>(nextPrintArg(args));
                crtFloatFormatters.format(&value, output, capacity, ch, precision, capital, &crtPrintLocale);
                if ((flags & Alternate) && precision == 0)
                    crtFloatFormatters.forceDecimal(output, &crtPrintLocale);
                if (ch == 'g' && !(flags & Alternate))
                    crtFloatFormatters.cropZeros(output, &crtPrintLocale);
                text = output;
                if (*text == '-') { flags |= Negative; ++text; }
                length = 0;
                while (text[length]) ++length;
                break;
            }
            case 'd': case 'i': flags |= Signed; integer = true; break;
            case 'u': integer = true; break;
            case 'p': precision = 8; [[fallthrough]];
            case 'X': hexOffset = 7; radix = 16; integer = true; break;
            case 'x': hexOffset = 39; radix = 16; integer = true; break;
            case 'o': radix = 8; integer = true; if (flags & Alternate) flags |= Octal; break;
            }
            if (integer) {
                if (radix == 16 && (flags & Alternate)) {
                    prefix[0] = '0'; prefix[1] = static_cast<unsigned char>(hexOffset + 81);
                    prefixLength = 2;
                }
                uint64_t value;
                if (flags & (Int64 | LongLong))
                    value = *reinterpret_cast<const uint64_t*>(nextPrintArg(args));
                else {
                    uint32_t word = printWord(args);
                    if (flags & Short) {
                        value = flags & Signed ? static_cast<uint64_t>(static_cast<int64_t>(static_cast<int16_t>(word)))
                                               : static_cast<uint16_t>(word);
                    } else {
                        value = flags & Signed ? static_cast<uint64_t>(static_cast<int64_t>(static_cast<int32_t>(word)))
                                               : word;
                    }
                }
                if ((flags & Signed) && static_cast<int64_t>(value) < 0) {
                    value = 0 - value;
                    flags |= Negative;
                }
                if (!(flags & (Int64 | LongLong))) value &= 0xFFFFFFFFu;
                if (precision < 0) precision = 1;
                else { flags &= ~Zero; if (precision > 512) precision = 512; }
                if (value == 0) prefixLength = 0;
                // Digits grow backwards, as in the original stack buffer.
                unsigned char* end = buffer + sizeof(buffer);
                unsigned char* digits = end;
                while (precision-- > 0 || value != 0) {
                    unsigned digit = static_cast<unsigned>(value % radix) + '0';
                    value /= radix;
                    if (digit > '9') digit += hexOffset;
                    *--digits = static_cast<unsigned char>(digit);
                }
                length = static_cast<int>(end - digits);
                text = digits;
                if ((flags & Octal) && (length == 0 || *text != '0')) {
                    *--digits = '0'; text = digits; ++length;
                }
            }
            if (!suppress) {
                if (flags & Signed) {
                    if (flags & Negative) { prefix[0] = '-'; prefixLength = 1; }
                    else if (flags & Plus) { prefix[0] = '+'; prefixLength = 1; }
                    else if (flags & Space) { prefix[0] = ' '; prefixLength = 1; }
                }
                const int padding = width - length - prefixLength;
                if (!(flags & (Left | Zero))) {
                    for (int i = padding; i > 0; --i) {
                        crtWriteChar(' ', stream, &count);
                        if (count == -1) break;
                    }
                }
                crtWriteBlock(prefix, prefixLength, stream, &count);
                if ((flags & Zero) && !(flags & Left)) {
                    for (int i = padding; i > 0; --i) {
                        crtWriteChar('0', stream, &count);
                        if (count == -1) break;
                    }
                }
                if (wide && length > 0) {
                    const auto* p = reinterpret_cast<const uint16_t*>(text);
                    for (int i = 0; i < length; ++i) {
                        int converted;
                        unsigned char bytes[6];
                        if (crtWideCharToMultibyte(&converted, bytes, 6, p[i]) != 0 || converted == 0) {
                            count = -1;
                            break;
                        }
                        crtWriteBlock(bytes, converted, stream, &count);
                    }
                } else {
                    crtWriteBlock(text, length, stream, &count);
                }
                if (count >= 0 && (flags & Left)) {
                    for (int i = padding; i > 0; --i) {
                        crtWriteChar(' ', stream, &count);
                        if (count == -1) break;
                    }
                }
            }
            if (allocated) { crtFree(allocated); allocated = nullptr; }
            break;
        }
        }
    }
    return count;
}
