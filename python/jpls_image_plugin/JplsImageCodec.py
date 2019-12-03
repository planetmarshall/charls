import itertools
from ctypes import (
    cdll,
    c_uint8,
    c_uint16,
    c_int32,
    c_uint32,
    c_size_t,
    pointer,
    Structure,
)
from ctypes.util import find_library
from enum import IntEnum
import struct

from PIL.Image import Image
from PIL.ImageFile import PyDecoder
from PIL.ImageFile import ERRORS


class CharlsError(IntEnum):
    CHARLS_JPEGLS_ERRC_SUCCESS = 0,
    INVALID_ARGUMENT = 1,
    PARAMETER_VALUE_NOT_SUPPORTED = 2,
    DESTINATION_BUFFER_TOO_SMALL = 3,
    SOURCE_BUFFER_TOO_SMALL = 4,
    INVALID_ENCODED_DATA = 5,
    TOO_MUCH_ENCODED_DATA = 6,
    INVALID_OPERATION = 7,
    BIT_DEPTH_FOR_TRANSFORM_NOT_SUPPORTED = 8,
    COLOR_TRANSFORM_NOT_SUPPORTED = 9,
    ENCODING_NOT_SUPPORTED = 10,
    UNKNOWN_JPEG_MARKER_FOUND = 11,
    JPEG_MARKER_START_BYTE_NOT_FOUND = 12,
    NOT_ENOUGH_MEMORY = 13,
    UNEXPECTED_FAILURE = 14,
    START_OF_IMAGE_MARKER_NOT_FOUND = 15,
    START_OF_FRAME_MARKER_NOT_FOUND = 16,
    INVALID_MARKER_SEGMENT_SIZE = 17,
    DUPLICATE_START_OF_IMAGE_MARKER = 18,
    DUPLICATE_START_OF_FRAME_MARKER = 19,
    DUPLICATE_COMPONENT_ID_IN_SOF_SEGMENT = 20,
    UNEXPECTED_END_OF_IMAGE_MARKER = 21,
    INVALID_JPEGLS_PRESET_PARAMETER_TYPE = 22,
    JPEGLS_PRESET_EXTENDED_PARAMETER_TYPE_NOT_SUPPORTED = 23,
    MISSING_END_OF_SPIFF_DIRECTORY = 24,
    INVALID_ARGUMENT_WIDTH = 100,
    INVALID_ARGUMENT_HEIGHT = 101,
    INVALID_ARGUMENT_COMPONENT_COUNT = 102,
    INVALID_ARGUMENT_BITS_PER_SAMPLE = 103,
    INVALID_ARGUMENT_INTERLEAVE_MODE = 104,
    INVALID_ARGUMENT_NEAR_LOSSLESS = 105,
    INVALID_ARGUMENT_PC_PARAMETERS = 106,
    INVALID_ARGUMENT_SPIFF_ENTRY_SIZE = 110,
    INVALID_ARGUMENT_COLOR_TRANSFORMATION = 111,
    INVALID_PARAMETER_WIDTH = 200,
    INVALID_PARAMETER_HEIGHT = 201,
    INVALID_PARAMETER_COMPONENT_COUNT = 202,
    INVALID_PARAMETER_BITS_PER_SAMPLE = 203,
    INVALID_PARAMETER_INTERLEAVE_MODE = 204


class SpiffColorSpace(IntEnum):
    BI_LEVEL_BLACK = 0,
    YCBCR_ITU_BT_709_VIDEO = 1,
    NONE = 2,
    YCBCR_ITU_BT_601_1_RGB = 3,
    YCBCR_ITU_BT_601_1_VIDEO = 4,
    GRAYSCALE = 8,
    PHOTO_YCC = 9,
    RGB = 10,
    CMY = 11,
    CMYK = 12,
    YCCK = 13,
    CIE_LAB = 14,
    BI_LEVEL_WHITE = 15


class SpiffResolutionUnits(IntEnum):
    ASPECT_RATIO = 0,
    DOTS_PER_INCH = 1,
    DOTS_PER_CENTIMETER = 2


class InterleaveMode(IntEnum):
    NONE = 0,
    LINE = 1,
    SAMPLE = 2


class JplsImageDecoder(PyDecoder):
    def init(self, args):
        self._pulls_fd = True
        self._charls = cdll.LoadLibrary('/home/andrew/.local/lib/libcharls.so')
        self._decoder = self._charls.charls_jpegls_decoder_create()

    def decode(self, buffer):
        buffer = self.fd.read()
        source_size_bytes = len(buffer)
        err = self._charls.charls_jpegls_decoder_set_source_buffer(self._decoder, buffer, source_size_bytes)
        err = self._charls.charls_jpegls_decoder_read_header(self._decoder)
        return -1, 0

    def cleanup(self):
        self._charls.charls_jpegls_decoder_destroy(self._decoder)


class charls_frame_info(Structure):
    _fields_ = [("width", c_uint32),
                ("height", c_uint32),
                ("bits_per_sample", c_int32),
                ("component_count", c_int32)]

def _pixel_data(im, bits_per_component, number_of_components, interleave_mode=InterleaveMode.NONE):
    data = im.getdata()
    num_elements = number_of_components * len(data)
    if number_of_components == 1:
        flat_data = data
    else:
        if interleave_mode == InterleaveMode.SAMPLE:
            flat_data = itertools.chain.from_iterable(data)
        elif interleave_mode == InterleaveMode.NONE:
            rv = []
            gv = []
            bv = []
            for (r, g, b) in data:
                rv.append(r)
                gv.append(g)
                bv.append(b)
            flat_data = itertools.chain.from_iterable((rv, gv, bv))

    array_type = c_uint16 if bits_per_component > 8 else c_uint8
    return (array_type * num_elements)(*flat_data)

class JplsImageEncoder():
    def __init__(self):
        self._charls = cdll.LoadLibrary('/home/andrew/.local/lib/libcharls.so')
        self.encoder = self._charls.charls_jpegls_encoder_create()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def _estimate_encoded_size(self):
        encoded_buffer_size = c_size_t(0)
        error = self._charls.charls_jpegls_encoder_get_estimated_destination_size(
            self.encoder,
            pointer(encoded_buffer_size)
        )
        return encoded_buffer_size.value

    def _pixel_format(self, im):
        if im.mode == 'L':
            pf = 8, 1
        elif im.mode in ['I', 'I;16', 'I;16L', 'I;16B', 'I;16N']:
            pf = 16, 1
        elif im.mode == 'RGB':
            pf = 8, 3
        elif im.mode == 'RGBA':
            pf = 8, 4
        else:
            raise SyntaxError("Image Mode {} not supported".format(im.mode))

        bits_per_component = im.encoderinfo.get("bits_per_component", pf[0])
        return bits_per_component, pf[1]


    def encode(self, im: Image, fp):

        bits_per_component, components = self._pixel_format(im)
        frame_info = charls_frame_info(im.width, im.height, bits_per_component, components)
        error = self._charls.charls_jpegls_encoder_set_frame_info(self.encoder, pointer(frame_info))

        encoded_size = self._estimate_encoded_size()
        encoded_buffer = bytearray(encoded_size)
        encoded_buffer_type = c_uint8 * encoded_size

        error = self._charls.charls_jpegls_encoder_set_destination_buffer(
            self.encoder,
            encoded_buffer_type.from_buffer(encoded_buffer),
            encoded_size
        )

        if im.encoderinfo.get('spiff', True):
            error = self._charls.charls_jpegls_encoder_write_standard_spiff_header(
                self.encoder,
                c_int32(SpiffColorSpace.GRAYSCALE),
                c_int32(SpiffResolutionUnits.DOTS_PER_INCH.value),
                72,
                72
            )

        data = _pixel_data(im, bits_per_component, components)
        error = self._charls.charls_jpegls_encoder_encode_from_buffer(
            self.encoder,
            pointer(data),
            len(data),
            0
        )
        bytes_written = c_size_t(0)
        error = self._charls.charls_jpegls_encoder_get_bytes_written(
            self.encoder,
            pointer(bytes_written)
        )

        encoded_bytes = bytes_written.value

        fp.write(encoded_buffer[:encoded_bytes])

    def cleanup(self):
        self._charls.charls_jpegls_encoder_destroy(self.encoder)
