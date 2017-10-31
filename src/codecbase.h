//
// (C) CharLS Team 2017, all rights reserved. See the accompanying "License.txt" for licensed use.
//

#ifndef CHARLS_CODECBASE
#define CHARLS_CODECBASE

#include "publictypes.h"

namespace charls
{

class CodecBase
{
public:
    JlsParameters & Info() noexcept
    {
        return _params;
    }

    virtual void SetPresets(const JpegLSPresetCodingParameters& presets) = 0;

protected:
    explicit CodecBase(const JlsParameters& params) :
        _params(params)
    {
    }

    virtual ~CodecBase() = default;

    bool IsInterleaved() noexcept
    {
        if (Info().interleaveMode == InterleaveMode::None)
            return false;

        if (Info().components == 1)
            return false;

        return true;
    }


    JlsParameters _params;
    JlsRect _rect{};
};

}

#endif
