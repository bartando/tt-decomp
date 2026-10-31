/**
 * rage_stream_manager.hpp — stream buffer reset and tokenizer bootstrap helpers
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 */
#pragma once

#include <cstdint>
#include "rage/fi_stream.hpp"

namespace rage {

struct fiAsciiTokenizerState {
    ptr32<void> m_pVTable;
    std::uint32_t m_objectFlags;
    std::int32_t m_lineNumber;
    ptr32<fiStreamBuf> m_pInputStream;
    std::int32_t m_currentChar;
    std::int32_t m_parseMode;
    std::int32_t m_pushbackCount;
    char m_aPushbackBuffer[128];
    ptr32<const char> m_pAdditionalTokenDelimiters;
    std::int32_t m_parseScratchState;
};

void InitializeAsciiTokenizerState(fiAsciiTokenizerState* pTokenizerState);

} // namespace rage

extern "C" void rage_52B0_1(rage::fiAsciiTokenizerState* pTokenizerState);
