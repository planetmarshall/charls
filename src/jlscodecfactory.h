//
// (C) CharLS Team 2014, all rights reserved. See the accompanying "License.txt" for licensed use.
//

#ifndef CHARLS_JLSCODECFACTORY
#define CHARLS_JLSCODECFACTORY

#include "losslesstraits.h"
#include "defaulttraits.h"
#include "scan.h"
#include "publictypes.h"
#include <memory>

namespace charls
{

template<typename Strategy>
class JlsCodecFactory
{
public:
    std::unique_ptr<Strategy> CreateCodec(const JlsParameters& params, const JpegLSPresetCodingParameters& presets)
    {
        std::unique_ptr<Strategy> codec;

        if (presets.ResetValue == 0 || presets.ResetValue == DefaultResetValue)
        {
            codec = CreateOptimizedCodec(params);
        }
        else
        {
            if (params.bitsPerSample <= 8)
            {
                DefaultTraits<uint8_t, uint8_t> traits((1 << params.bitsPerSample) - 1, params.allowedLossyError, presets.ResetValue);
                traits.MAXVAL = presets.MaximumSampleValue;
                codec = std::make_unique<JlsCodec<DefaultTraits<uint8_t, uint8_t>, Strategy>>(traits, params);
            }
            else
            {
                DefaultTraits<uint16_t, uint16_t> traits((1 << params.bitsPerSample) - 1, params.allowedLossyError, presets.ResetValue);
                traits.MAXVAL = presets.MaximumSampleValue;
                codec = std::make_unique<JlsCodec<DefaultTraits<uint16_t, uint16_t>, Strategy>>(traits, params);
            }
        }

        if (codec)
        {
            codec->SetPresets(presets);
        }

        return codec;
    }

private:
    std::unique_ptr<Strategy> CreateOptimizedCodec(const JlsParameters& params)
    {
        if (params.interleaveMode == InterleaveMode::Sample && params.components != 3)
            return nullptr;

#ifndef DISABLE_SPECIALIZATIONS

        // optimized lossless versions common formats
        if (params.allowedLossyError == 0)
        {
            if (params.interleaveMode == InterleaveMode::Sample)
            {
                if (params.bitsPerSample == 8)
                    return create_codec(LosslessTraits<Triplet<uint8_t>, 8>(), params);
            }
            else
            {
                switch (params.bitsPerSample)
                {
                case  8: return create_codec(LosslessTraits<uint8_t, 8>(), params);
                case 12: return create_codec(LosslessTraits<uint16_t, 12>(), params);
                case 16: return create_codec(LosslessTraits<uint16_t, 16>(), params);
                default:
                    break;
                }
            }
        }

#endif

        const int maxval = (1 << params.bitsPerSample) - 1;

        if (params.bitsPerSample <= 8)
        {
            if (params.interleaveMode == InterleaveMode::Sample)
                return create_codec(DefaultTraits<uint8_t, Triplet<uint8_t> >(maxval, params.allowedLossyError), params);

            return create_codec(DefaultTraits<uint8_t, uint8_t>((1 << params.bitsPerSample) - 1, params.allowedLossyError), params);
        }
        if (params.bitsPerSample <= 16)
        {
            if (params.interleaveMode == InterleaveMode::Sample)
                return create_codec(DefaultTraits<uint16_t, Triplet<uint16_t> >(maxval, params.allowedLossyError), params);

            return create_codec(DefaultTraits<uint16_t, uint16_t>(maxval, params.allowedLossyError), params);
        }
        return nullptr;
    }

    template<typename Traits>
    std::unique_ptr<Strategy> create_codec(const Traits& traits, const JlsParameters& params)
    {
        return std::make_unique<JlsCodec<Traits, Strategy>>(traits, params);
    }
};

}
#endif
