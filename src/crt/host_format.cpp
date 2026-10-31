#include "crt/host_format.h"

#include <algorithm>
#include <cerrno>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <new>
#include <vector>

// Adapt native varargs, retaining the retail caller's truncation contract.
int _snprintf(char* buffer, size_t count, const char* format, ...) {
    if (!format || (!buffer && count != 0)) {
        errno = EINVAL;
        return -1;
    }
    va_list args;
    va_start(args, format);
    va_list measure;
    va_copy(measure, args);
    const int length = std::vsnprintf(nullptr, 0, format, measure);
    va_end(measure);
    if (length < 0) {
        va_end(args);
        return length;
    }
    const size_t stored = std::min(count, static_cast<size_t>(length));
    try {
        std::vector<char> text(stored + 1);
        const int result = std::vsnprintf(text.data(), text.size(), format, args);
        va_end(args);
        if (result < 0) return result;
        // The temporary terminator must not overwrite the last character when
        // length == count, or add a terminator when the output was truncated.
        const size_t copied = stored + (static_cast<size_t>(length) < count ? 1 : 0);
        if (copied != 0) std::memcpy(buffer, text.data(), copied);
        return static_cast<size_t>(length) > count ? -1 : length;
    } catch (const std::bad_alloc&) {
        va_end(args);
        errno = ENOMEM;
        return -1;
    }
}
