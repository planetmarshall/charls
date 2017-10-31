//
// (C) Jan de Vaan 2007-2010, all rights reserved. See the accompanying "License.txt" for licensed use.
//

#include "util.h"
#include "decoderstrategy.h"
#include "lookuptable.h"
#include "jlscodecfactory.h"
#include "jpegstreamreader.h"
#include "scan.h"
#include <vector>

namespace
{

signed char QuantizeGratientOrg(const JpegLSPresetCodingParameters& preset, int32_t NEAR, int32_t Di) noexcept
{
    if (Di <= -preset.Threshold3) return  -4;
    if (Di <= -preset.Threshold2) return  -3;
    if (Di <= -preset.Threshold1) return  -2;
    if (Di < -NEAR)  return  -1;
    if (Di <=  NEAR) return   0;
    if (Di < preset.Threshold1)   return   1;
    if (Di < preset.Threshold2)   return   2;
    if (Di < preset.Threshold3)   return   3;

    return  4;
}


std::vector<signed char> CreateQLutLossless(int32_t cbit)
{
    const JpegLSPresetCodingParameters preset = ComputeDefault((1 << cbit) - 1, 0);
    const int32_t range = preset.MaximumSampleValue + 1;

    std::vector<signed char> lut(range * 2);

    for (int32_t diff = -range; diff < range; diff++)
    {
        lut[range + diff] = QuantizeGratientOrg(preset, 0,diff);
    }
    return lut;
}

template<typename Strategy, typename Traits>
std::unique_ptr<Strategy> create_codec(const Traits& traits, const JlsParameters& params)
{
    return std::make_unique<JlsCodec<Traits, Strategy>>(traits, params);
}


// Functions to build tables used to decode short Golomb codes.

constexpr std::pair<int32_t, int32_t> CreateEncodedValue(int32_t k, int32_t mappedError)
{
    const int32_t highbits = mappedError >> k;
    return std::make_pair(highbits + k + 1, (int32_t(1) << k) | (mappedError & ((int32_t(1) << k) - 1)));
}


constexpr GolombCodeTable CreateTable(int32_t k)
{
    GolombCodeTable table;
    for (short nerr = 0; ; nerr++)
    {
        // Q is not used when k != 0
        const int32_t merrval = charls::GetMappedErrVal(nerr);
        const std::pair<int32_t, int32_t> paircode = CreateEncodedValue(k, merrval);
        if (paircode.first > GolombCodeTable::byte_bit_count)
            break;

        const GolombCode code(nerr, static_cast<short>(paircode.first));
        table.AddEntry(static_cast<uint8_t>(paircode.second), code);
    }

    for (short nerr = -1; ; nerr--)
    {
        // Q is not used when k != 0
        const int32_t merrval = charls::GetMappedErrVal(nerr);
        const std::pair<int32_t, int32_t> paircode = CreateEncodedValue(k, merrval);
        if (paircode.first > GolombCodeTable::byte_bit_count)
            break;

        const GolombCode code = GolombCode(nerr, static_cast<short>(paircode.first));
        table.AddEntry(static_cast<uint8_t>(paircode.second), code);
    }

    return table;
}


} // namespace


class charls_category : public std::error_category
{
public:
    const char* name() const noexcept override
    {
        return "charls";
    }

    std::string message(int /* errval */) const override
    {
        return "CharLS error";
    }
};

const std::error_category& charls_error::CharLSCategoryInstance() noexcept
{
    static charls_category instance;
    return instance;
}


// Lookup tables to replace code with lookup tables.
// To avoid threading issues, all tables are created when the program is loaded.

// Lookup table: decode symbols that are smaller or equal to 8 bit (16 tables for each value of k)
const GolombCodeTable decodingTables[16] = { CreateTable(0), CreateTable(1), CreateTable(2), CreateTable(3),
                              CreateTable(4), CreateTable(5), CreateTable(6), CreateTable(7),
                              CreateTable(8), CreateTable(9), CreateTable(10), CreateTable(11),
                              CreateTable(12), CreateTable(13), CreateTable(14),CreateTable(15) };

// Lookup tables: sample differences to bin indexes.
std::vector<signed char> rgquant8Ll = CreateQLutLossless(8);
std::vector<signed char> rgquant10Ll = CreateQLutLossless(10);
std::vector<signed char> rgquant12Ll = CreateQLutLossless(12);
std::vector<signed char> rgquant16Ll = CreateQLutLossless(16);
