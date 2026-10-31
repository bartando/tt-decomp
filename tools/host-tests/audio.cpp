#include "platform/audio.hpp"
#include <cassert>
#include <cstdio>
int main() {
    float samples[4*256];
    for(float& sample:samples) sample=7;
    AudioFrameBuffer buffer{};
    buffer.capacity={0,4,0,48000};
    buffer.frame={0,1,0,48000,samples};
    AudioFrame frame{};
    assert(PcmFrame_Get(&buffer,&frame)==0 && frame.samples==samples && frame.channels==1);
    assert(XAudioFrame_Get(&buffer.kind,&frame)==0 && frame.sampleRate==48000);
    frame.channels=2;
    assert(PcmFrame_Resize(&buffer,&frame,2)==0);
    assert(buffer.frame.channels==2 && samples[255]==7 && samples[256]==0 && samples[511]==0 && samples[512]==7);
    frame.channels=1;
    assert(PcmFrame_Resize(&buffer,&frame,0)==static_cast<int32_t>(0x8000FFFFu));
    assert(XAudioFrame_Resize(&buffer.kind,&frame,3)==0);
    frame.channels=5;
    assert(PcmFrame_Resize(&buffer,&frame,1)==static_cast<int32_t>(0x8007000Eu));
    frame.sampleRate=0;
    assert(PcmFrame_Resize(&buffer,&frame,1)==HostMediaInvalidArgument);
    const void* output=samples;
    assert(!XmaDecoder_IsEnabled(&buffer));
    assert(XmaDecoder_Lock(&buffer)==HostMediaNotSupported);
    assert(XmaDecoder_SubmitData(&buffer,0,samples,sizeof(samples))==HostMediaNotSupported);
    assert(XmaDecoder_SetReadPosition(&buffer,0,0,0)==HostMediaNotSupported);
    assert(XmaDecoder_SetLoopRegion(&buffer,0,nullptr)==HostMediaNotSupported);
    assert(!XmaDecoder_Available(&buffer,0));
    assert(!XmaDecoder_Peek(&buffer,0,&output) && !output);
    assert(XAudio_UInt64ToDouble(1ULL<<63)==0x1p63);
    assert(XAudio_UInt64ToDouble(~0ULL)==0x1p64);
    std::puts("PASS native audio frame bounds/flags/interface and explicit XMA rejection");
}
