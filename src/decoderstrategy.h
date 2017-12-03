//
// (C) Jan de Vaan 2007-2010, all rights reserved. See the accompanying "License.txt" for licensed use.
//

#ifndef CHARLS_DECODERSTATEGY
#define CHARLS_DECODERSTATEGY


#include "util.h"
#include "processline.h"
#include "jpegmarkercode.h"
#include "codecbase.h"
#include <memory>

namespace charls
{

inline bool ContainsFF(size_t n)
{
    return static_cast<uint8_t>(n) == 0xFF ||
        static_cast<uint8_t>(n >> 8) == 0xFF ||
        static_cast<uint8_t>(n >> 16) == 0xFF ||
        static_cast<uint8_t>(n >> 24) == 0xFF;
}

#if 0
inline bool ReadAndCheckFF(const uint8_t *p, size_t& value)
{
    size_t nextCache = p[0];
    if (nextCache == 0xFF)
        return false;

    uint8_t nextByte = p[1];
    if (nextByte == 0xFF)
        return false;

    nextCache = (nextCache << 8) | nextByte;
    nextByte = p[2];
    if (nextByte == 0xFF)
        return false;

    nextCache = (nextCache << 8) | nextByte;

    nextByte = p[3];
    if (nextByte == 0xFF)
        return false;

    return true;
}
#endif

inline size_t ReadAndCheckFF2(const uint8_t *p)
{
    size_t nextCache = *p;
    if (nextCache == 0xFF)
        return 0xFF;

    p++;
    uint8_t nextByte = *p;
    if (nextByte == 0xFF)
        return 0xFF;

    nextCache = (nextCache << 8) | nextByte;

    p++;
    nextByte = *p;
    if (nextByte == 0xFF)
        return 0xFF;

    nextCache = (nextCache << 8) | nextByte;

    p++;
    nextByte = *p;
    if (nextByte == 0xFF)
        return 0xFF;

    nextCache = (nextCache << 8) | nextByte;
    return nextCache;
}


// Purpose: Implements encoding to stream of bits. In encoding mode JpegLsCodec inherits from EncoderStrategy
class DecoderStrategy : public CodecBase
{
public:
    virtual std::unique_ptr<ProcessLine> CreateProcess(ByteStreamInfo rawStreamInfo) = 0;

    virtual void DoScan() = 0;

    void DecodeScan(std::unique_ptr<ProcessLine> processLine, const JlsRect& rect, ByteStreamInfo& compressedData)
    {
        _processLine = std::move(processLine);

        uint8_t* compressedBytes = const_cast<uint8_t*>(static_cast<const uint8_t*>(compressedData.rawData));
        _rect = rect;

        Init(compressedData);
        DoScan();
        SkipBytes(compressedData, GetCurBytePos() - compressedBytes);
    }

    void Init(ByteStreamInfo& compressedStream)
    {
        validCacheBitCount_ = 0;
        _readCache = 0;

        if (compressedStream.rawStream)
        {
            _buffer.resize(40000);
            _position = _buffer.data();
            _endPosition = _position;
            _byteStream = compressedStream.rawStream;
            AddBytesFromStream();
        }
        else
        {
            _byteStream = nullptr;
            _position = compressedStream.rawData;
            _endPosition = _position + compressedStream.count;
        }

        FillReadCache();
    }

    void AddBytesFromStream()
    {
        if (!_byteStream || _byteStream->sgetc() == std::char_traits<char>::eof())
            return;

        const std::size_t count = _endPosition - _position;

        if (count > 64)
            return;

        for (std::size_t i = 0; i < count; ++i)
        {
            _buffer[i] = _position[i];
        }
        const std::size_t offset = _buffer.data() - _position;

        _position += offset;
        _endPosition += offset;

        const std::streamsize readbytes = _byteStream->sgetn(reinterpret_cast<char*>(_endPosition), _buffer.size() - count);
        _endPosition += readbytes;
    }

    FORCE_INLINE void Skip(int32_t length) noexcept
    {
        validCacheBitCount_ -= length;
        _readCache = _readCache << length;
    }

    static void OnLineBegin(int32_t /*cpixel*/, void* /*ptypeBuffer*/, int32_t /*pixelStride*/) noexcept
    {
    }

    void OnLineEnd(int32_t pixelCount, const void* ptypeBuffer, int32_t pixelStride) const
    {
        _processLine->NewLineDecoded(ptypeBuffer, pixelCount, pixelStride);
    }

    void EndScan()
    {
        if (*_position != static_cast<uint8_t>(JpegMarkerCode::Start))
        {
            ReadBit();

            if (*_position != static_cast<uint8_t>(JpegMarkerCode::Start))
                throw charls_error(charls::ApiResult::TooMuchCompressedData);
        }

        if (_readCache != 0)
            throw charls_error(charls::ApiResult::TooMuchCompressedData);
    }

    uint8_t* GetCurBytePos() const noexcept
    {
        int32_t validBits = validCacheBitCount_;
        uint8_t* compressedBytes = _position;

        for (;;)
        {
            const int32_t cbitLast = compressedBytes[-1] == static_cast<uint8_t>(JpegMarkerCode::Start) ? 7 : 8;

            if (validBits < cbitLast)
                return compressedBytes;

            validBits -= cbitLast;
            compressedBytes--;
        }
    }

    FORCE_INLINE int32_t ReadValue(int32_t length)
    {
        if (validCacheBitCount_ < length)
        {
            FillReadCache();
            if (validCacheBitCount_ < length)
                throw charls_error(charls::ApiResult::InvalidCompressedData);
        }

        ASSERT(length != 0 && length <= validCacheBitCount_);
        ASSERT(length < 32);
        const int32_t result = static_cast<int32_t>(_readCache >> (readCache_bit_count - length));
        Skip(length);
        return result;
    }

    FORCE_INLINE int32_t PeekByte()
    {
        if (validCacheBitCount_ < 8)
        {
            FillReadCache();
        }

        return static_cast<int32_t>(_readCache >> (readCache_bit_count - 8));
    }

    FORCE_INLINE bool ReadBit()
    {
        if (validCacheBitCount_ <= 0)
        {
            FillReadCache();
        }

        const bool bSet = (_readCache & (std::size_t(1) << (readCache_bit_count - 1))) != 0;
        Skip(1);
        return bSet;
    }

    FORCE_INLINE int32_t Peek0Bits()
    {
        if (validCacheBitCount_ < 16)
        {
            FillReadCache();
        }
        std::size_t valTest = _readCache;

        for (int32_t count = 0; count < 16; count++)
        {
            if ((valTest & (std::size_t(1) << (readCache_bit_count - 1))) != 0)
                return count;

            valTest <<= 1;
        }
        return -1;
    }

    FORCE_INLINE int32_t ReadHighbits()
    {
        const int32_t count = Peek0Bits();
        if (count >= 0)
        {
            Skip(count + 1);
            return count;
        }
        Skip(15);

        for (int32_t highbits = 15; ; highbits++)
        {
            if (ReadBit())
                return highbits;
        }
    }

    int32_t ReadLongValue(int32_t length)
    {
        if (length <= 24)
            return ReadValue(length);

        return (ReadValue(length - 24) << 24) + ReadValue(24);
    }

protected:
    explicit DecoderStrategy(const JlsParameters& params) :
        CodecBase(params)
    {
    }

    std::unique_ptr<ProcessLine> _processLine;

private:
    void FillReadCache()
    {
        ASSERT(static_cast<size_t>(validCacheBitCount_) <= readCache_bit_count - 8);

        if (OptimizedFill())
            return;

        FillReadCacheNotFast();
    }

    void FillReadCacheNotFast()
    {
        AddBytesFromStream();

        do
        {
            if (_position >= _endPosition)
            {
                if (validCacheBitCount_ <= 0)
                    throw charls_error(charls::ApiResult::InvalidCompressedData);

                return;
            }

            const std::size_t valnew = _position[0];

            if (valnew == static_cast<std::size_t>(JpegMarkerCode::Start))
            {
                // JPEG bit stream rule: no FF may be followed by 0x80 or higher
                if (_position == _endPosition - 1 || (_position[1] & 0x80) != 0)
                {
                    if (validCacheBitCount_ <= 0)
                        throw charls_error(charls::ApiResult::InvalidCompressedData);

                    return;
                }
            }

            _readCache |= valnew << (readCache_bit_count - 8 - validCacheBitCount_);
            _position += 1;
            validCacheBitCount_ += 8;

            if (valnew == static_cast<std::size_t>(JpegMarkerCode::Start))
            {
                validCacheBitCount_--;
            }
        } while (static_cast<size_t>(validCacheBitCount_) < readCache_bit_count - 8);
    }

    FORCE_INLINE bool OptimizedFill() noexcept
    {
        // Easy & fast: if there is no 0xFF byte in sight, we can read without bit stuffing
        if (_position < _endPosition - sizeof _readCache)
        {
            uint8_t *p = _position;

            size_t nextCache = *p;
            if (nextCache == 0xFF)
                return false;

            p++;
            uint8_t nextByte = *p;
            if (nextByte == 0xFF)
                return false;

            nextCache = (nextCache << 8) | nextByte;

            p++;
            nextByte = *p;
            if (nextByte == 0xFF)
                return false;

            nextCache = (nextCache << 8) | nextByte;

            p++;
            nextByte = *p;
            if (nextByte == 0xFF)
                return false;

            nextCache = (nextCache << 8) | nextByte;

            _readCache |= nextCache >> validCacheBitCount_;
            const size_t bytesAddedToCache = (readCache_bit_count - validCacheBitCount_) / 8;
            _position += bytesAddedToCache;
            validCacheBitCount_ += bytesAddedToCache * 8;
            ASSERT(static_cast<size_t>(validCacheBitCount_) >= readCache_bit_count - 8);
            return true;
        }
        return false;
    }

    static constexpr size_t readCache_bit_count = sizeof(std::size_t) * 8;

    std::vector<uint8_t> _buffer;
    std::basic_streambuf<char>* _byteStream{};

    std::size_t _readCache{};
    int32_t validCacheBitCount_{};
    uint8_t* _position{};
    uint8_t* _endPosition{};
};

}
#endif
