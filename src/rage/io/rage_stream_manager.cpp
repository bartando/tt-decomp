/**
 * rage_stream_manager.cpp — stream buffer reset and tokenizer bootstrap logic
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 */

#include "rage/rage_stream_manager.hpp"

namespace rage {

void InitializeAsciiTokenizerState(fiAsciiTokenizerState* pTokenizerState) {
    if (pTokenizerState == nullptr) {
        return;
    }

    if (pTokenizerState->m_pInputStream != nullptr) {
        fiStreamBuf_Reset(pTokenizerState->m_pInputStream.get(), 0);
    }

    pTokenizerState->m_pushbackCount = 0;
    pTokenizerState->m_lineNumber = 1;
    pTokenizerState->m_currentChar = ' ';
    pTokenizerState->m_aPushbackBuffer[0] = '\0';
    pTokenizerState->m_parseScratchState = 0;
    pTokenizerState->m_parseMode = 2;
}

} // namespace rage

extern "C" void rage_52B0_1(rage::fiAsciiTokenizerState* pTokenizerState) {
    rage::InitializeAsciiTokenizerState(pTokenizerState);
}
