// Copyright (c) Team CharLS. All rights reserved. See the accompanying "LICENSE.md" for licensed use.

#pragma once

#include <charls/public_types.h>
#include <cstdint>
#include <vector>

namespace charls
{

enum class JpegMarkerCode : uint8_t;

JpegLSPresetCodingParameters ComputeDefault(int32_t maximumSampleValue, int32_t allowedLossyError) noexcept;

// Purpose: minimal implementation to read a JPEG byte stream.
class JpegStreamReader final
{
public:
    explicit JpegStreamReader(ByteStreamInfo byteStreamInfo) noexcept;

    const JlsParameters& GetMetadata() const noexcept
    {
        return params_;
    }

    const JpegLSPresetCodingParameters& GetCustomPreset() const noexcept
    {
        return params_.custom;
    }

    void Read(ByteStreamInfo rawPixels);
    void ReadHeader();

    void SetInfo(const JlsParameters& params) noexcept
    {
        params_ = params;
    }

    void SetRect(const JlsRect& rect) noexcept
    {
        rect_ = rect;
    }

    void ReadStartOfScan(bool firstComponent);
    uint8_t ReadByte();

private:
    int ReadUInt16();
    int32_t ReadSegmentSize();
    void ReadNBytes(std::vector<char>& dst, int byteCount);
    JpegMarkerCode ReadNextMarkerCode();
    void ValidateMarkerCode(JpegMarkerCode markerCode) const;

    int ReadMarkerSegment(JpegMarkerCode markerCode, int32_t segmentSize);
    int ReadStartOfFrameSegment(int32_t segmentSize);
    static int ReadComment() noexcept;
    int ReadPresetParameters();
    void ReadJfif();
    int TryReadHPColorTransformSegment(int32_t segmentSize);

    ByteStreamInfo byteStream_;
    JlsParameters params_;
    JlsRect rect_;
};

} // namespace charls