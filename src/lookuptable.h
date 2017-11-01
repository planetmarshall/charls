//
// (C) Jan de Vaan 2007-2010, all rights reserved. See the accompanying "License.txt" for licensed use.
//

#ifndef CHARLS_LOOKUPTABLE
#define CHARLS_LOOKUPTABLE

#include "util.h"


/// <summary>Golomb code and its bit count. Used by the golomb code lookup table.</summary>
struct GolombCode
{
    GolombCode() = default;

    constexpr GolombCode(int32_t value, int32_t bit_count) :
        value_(value),
        bit_count_(bit_count)
    {
    }

    constexpr int32_t GetValue() const
    {
        return value_;
    }

    constexpr int32_t GetBitCount() const
    {
        return bit_count_;
    }

private:
    int32_t value_{};
    int32_t bit_count_{};
};


class GolombCodeTable
{
public:
    static constexpr size_t byte_bit_count = 8;

    constexpr void AddEntry(uint8_t bvalue, GolombCode code)
    {
        const int32_t bit_count = code.GetBitCount();
        ASSERT(static_cast<size_t>(bit_count) <= byte_bit_count);

        for (int32_t i = 0; i < 1 << (byte_bit_count - bit_count); ++i)
        {
            ASSERT(codes_[(bvalue << (byte_bit_count - bit_count)) + i].GetBitCount() == 0);
            codes_[(bvalue << (byte_bit_count - bit_count)) + i] = code;
        }
    }

    FORCE_INLINE const GolombCode& Get(int32_t value) const noexcept
    {
        return codes_[value];
    }

private:
    GolombCode codes_[1 << byte_bit_count]{};
};

#endif
