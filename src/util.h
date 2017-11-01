//
// (C) Jan de Vaan 2007-2010, all rights reserved. See the accompanying "License.txt" for licensed use.
//


#ifndef CHARLS_UTIL
#define CHARLS_UTIL

#include "publictypes.h"
#include "constants.h"
#include <vector>
#include <system_error>
#include <memory>
#include <algorithm>
// ReSharper disable once CppUnusedIncludeDirective
#include <cassert>

// Use an uppercase alias for assert to make it clear that it is a pre-processor macro.
#define ASSERT(t) assert(t)

// Only use __forceinline for the Microsoft C++ compiler in release mode (verified scenario)
// Use the build-in optimizer for all other C++ compilers.
// Note: usage of FORCE_INLINE may be reduced in the future as the latest generation of C++ compilers
// can handle optimization by themselves.
#ifndef FORCE_INLINE
#  ifdef _MSC_VER
#    ifdef NDEBUG
#      define FORCE_INLINE __forceinline
#    else
#      define FORCE_INLINE
#    endif
#  else
#    define FORCE_INLINE
#  endif
#endif


constexpr size_t int32_t_bit_count = sizeof(int32_t) * 8;


inline void push_back(std::vector<uint8_t>& values, uint16_t value)
{
    values.push_back(uint8_t(value / 0x100));
    values.push_back(uint8_t(value % 0x100));
}


constexpr int32_t log_2(int32_t n) noexcept
{
    int32_t x = 0;
    while (n > (int32_t(1) << x))
    {
        ++x;
    }
    return x;
}


constexpr int32_t Sign(int32_t n) noexcept
{
    return (n >> (int32_t_bit_count - 1)) | 1;
}


constexpr int32_t BitWiseSign(int32_t i) noexcept
{
    return i >> (int32_t_bit_count - 1);
}


template<typename T>
struct Triplet
{
    Triplet() :
        v1(0),
        v2(0),
        v3(0)
    {}

    Triplet(int32_t x1, int32_t x2, int32_t x3) noexcept :
        v1(static_cast<T>(x1)),
        v2(static_cast<T>(x2)),
        v3(static_cast<T>(x3))
    {}

    union
    {
        T v1;
        T R;
    };
    union
    {
        T v2;
        T G;
    };
    union
    {
        T v3;
        T B;
    };
};


inline bool operator==(const Triplet<uint8_t>& lhs, const Triplet<uint8_t>& rhs) noexcept
{
    return lhs.v1 == rhs.v1 && lhs.v2 == rhs.v2 && lhs.v3 == rhs.v3;
}


inline bool operator!=(const Triplet<uint8_t>& lhs, const Triplet<uint8_t>& rhs) noexcept
{
    return !(lhs == rhs);
}


template<typename sample>
struct Quad : Triplet<sample>
{
    Quad() :
        v4(0)
        {}

    Quad(Triplet<sample> triplet, int32_t alpha) noexcept : Triplet<sample>(triplet), A(static_cast<sample>(alpha))
        {}

    union
    {
        sample v4;
        sample A;
    };
};


template<int size>
struct FromBigEndian
{
};


template<>
struct FromBigEndian<4>
{
    FORCE_INLINE static unsigned int Read(const uint8_t* pbyte) noexcept
    {
        return (pbyte[0] << 24) + (pbyte[1] << 16) + (pbyte[2] << 8) + (pbyte[3] << 0);
    }
};


template<>
struct FromBigEndian<8>
{
    FORCE_INLINE static uint64_t Read(const uint8_t* pbyte) noexcept
    {
        return (static_cast<uint64_t>(pbyte[0]) << 56) + (static_cast<uint64_t>(pbyte[1]) << 48) +
               (static_cast<uint64_t>(pbyte[2]) << 40) + (static_cast<uint64_t>(pbyte[3]) << 32) +
               (static_cast<uint64_t>(pbyte[4]) << 24) + (static_cast<uint64_t>(pbyte[5]) << 16) +
               (static_cast<uint64_t>(pbyte[6]) <<  8) + (static_cast<uint64_t>(pbyte[7]) << 0);
    }
};


class charls_error : public std::system_error
{
public:
    explicit charls_error(charls::ApiResult errorCode)
        : system_error(static_cast<int>(errorCode), CharLSCategoryInstance())
    {
    }


    charls_error(charls::ApiResult errorCode, const std::string& message)
        : system_error(static_cast<int>(errorCode), CharLSCategoryInstance(), message)
    {
    }

private:
    static const std::error_category& CharLSCategoryInstance() noexcept;
};


inline void SkipBytes(ByteStreamInfo& streamInfo, std::size_t count) noexcept
{
    if (!streamInfo.rawData)
        return;

    streamInfo.rawData += count;
    streamInfo.count -= count;
}


template<typename T>
std::ostream& operator<<(typename std::enable_if<std::is_enum<T>::value, std::ostream>::type& stream, const T& e)
{
    return stream << static_cast<typename std::underlying_type<T>::type>(e);
}

/// <summary>Clamping function as defined by ISO/IEC 14495-1, Figure C.3</summary>
constexpr int32_t clamp(int32_t i, int32_t j, int32_t maximumSampleValue) noexcept
{
    if (i > maximumSampleValue || i < j)
        return j;

    return i;
}

constexpr JpegLSPresetCodingParameters ComputeDefault(int32_t maximumSampleValue, int32_t allowedLossyError) noexcept
{
    const int32_t factor = (std::min(maximumSampleValue, 4095) + 128) / 256;
    const int threshold1 = clamp(factor * (DefaultThreshold1 - 2) + 2 + 3 * allowedLossyError, allowedLossyError + 1, maximumSampleValue);
    const int threshold2 = clamp(factor * (DefaultThreshold2 - 3) + 3 + 5 * allowedLossyError, threshold1, maximumSampleValue); //-V537
    const int threshold3 = clamp(factor * (DefaultThreshold3 - 4) + 4 + 7 * allowedLossyError, threshold2, maximumSampleValue);

    return { maximumSampleValue, threshold1, threshold2, threshold3, DefaultResetValue };
}


#endif
