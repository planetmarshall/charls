import itertools
from ctypes import (
    windll,
    cdll,
    c_uint8,
    c_uint16,
    c_int32,
    c_uint32,
    c_size_t,
    c_void_p,
    pointer,
    Structure,
)
import ctypes.util
from enum import IntEnum
from itertools import chain
import os
import platform


from PIL.Image import Image
from PIL.ImageFile import PyDecoder


class InterleaveMode(IntEnum):
    NONE = 0,
    LINE = 1,
    SAMPLE = 2


class CharlsErrorCode(IntEnum):
    SUCCESS = 0,
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


class CharlsError(Exception):
    def __init__(self, charls_error_code):
        self.message = charls_error_code.name
        self.error_code = charls_error_code


def _interleave_pixels(pixels, interleave_step):
    component_index = list(range(0, len(pixels)+1, interleave_step))
    return chain.from_iterable(zip(*(pixels[a:b] for (a, b) in zip(component_index[:-1], component_index[1:]))))


def _interleave_decoded_pixels(pixels, num_components, interleave_mode):
    if interleave_mode == InterleaveMode.NONE:
        return _interleave_pixels(pixels, len(pixels)//num_components)
    else:
        return pixels


def _interleave_pixels_for_encoding(pixels, num_components, interleave_mode):
    if interleave_mode == InterleaveMode.NONE:
        return _interleave_pixels(pixels, num_components)
    else:
        return pixels


def _encode_pixels(pixels, bits_per_component):
    if bits_per_component <= 8:
        return bytes(pixels)


def _pixel_data_for_encoding(im, bits_per_component, number_of_components, interleave_mode):
    data = im.getdata()
    num_elements = number_of_components * len(data)
    if number_of_components == 1:
        flat_data = data
    else:
        flat_data = _interleave_pixels_for_encoding(
            list(itertools.chain.from_iterable(data)),
            num_components=number_of_components,
            interleave_mode=interleave_mode)

    array_type = c_uint16 if bits_per_component > 8 else c_uint8
    return (array_type * num_elements)(*flat_data)


def _find_charls():
    if 'CHARLS_LIBRARY' in os.environ:
        return os.environ['CHARLS_LIBRARY']
    if platform.system() == 'Windows':
        bits, linkage = platform.architecture()
        lib_name = {
            '64bit': 'charls-2-x64',
            '32bit': 'charls-2-x86'
        }
        return ctypes.util.find_library(lib_name[bits])

    return 'libcharls.so'


def _load_charls():
    try:
        if platform.system() == "Windows":
            return windll.LoadLibrary(_find_charls())
        return cdll.LoadLibrary(_find_charls())
    except Exception as err:
        raise OSError("Couldn't load charls shared library. "
                      "Ensure it is in the PATH or set the CHARLS_LIBRARY environment variable to its full path.", err)


class JplsImageDecoder(PyDecoder):
    def __init__(self, mode, *args):
        super().__init__(mode, *args)
        self._pulls_fd = True
        self._charls = _load_charls()
        self._charls.charls_jpegls_decoder_create.restype = c_void_p
        self._decoder = c_void_p(self._charls.charls_jpegls_decoder_create())

    def call_charls_decode(self, fn, *args):
        err = fn(self._decoder, *args)
        if err != CharlsErrorCode.SUCCESS:
            raise CharlsError(CharlsErrorCode(err))

    def decode(self, buffer):
        buffer = bytearray(self.fd.read())
        source_size_bytes = len(buffer)
        source_buffer = (c_uint8 * source_size_bytes).from_buffer(buffer)
        self.call_charls_decode(self._charls.charls_jpegls_decoder_set_source_buffer, pointer(source_buffer), source_size_bytes)
        self.call_charls_decode(self._charls.charls_jpegls_decoder_read_header)
        frame_info = FrameInfo()
        self.call_charls_decode(self._charls.charls_jpegls_decoder_get_frame_info, pointer(frame_info))
        interleave_mode = c_int32()
        self.call_charls_decode(self._charls.charls_jpegls_decoder_get_interleave_mode, pointer(interleave_mode))
        destination_size = c_size_t(0)
        self.call_charls_decode(self._charls.charls_jpegls_decoder_get_destination_size, pointer(destination_size))
        destination_buffer = (c_uint8 * destination_size.value)()
        self.call_charls_decode(
            self._charls.charls_jpegls_decoder_decode_to_buffer,
            pointer(destination_buffer),
            destination_size.value,
            0
        )
        raw_pixels = destination_buffer if frame_info.component_count == 1 else _encode_pixels(
            _interleave_decoded_pixels(
                destination_buffer,
                num_components=frame_info.component_count,
                interleave_mode=InterleaveMode(interleave_mode.value)
            ), frame_info.bits_per_sample)

        self.set_as_raw(raw_pixels)
        return -1, 0

    def cleanup(self):
        self._charls.charls_jpegls_decoder_destroy(self._decoder)


class FrameInfo(Structure):
    _fields_ = [("width", c_uint32),
                ("height", c_uint32),
                ("bits_per_sample", c_int32),
                ("component_count", c_int32)]


def _line_interleave_mode(mode):
    if mode is None:
        return InterleaveMode.NONE

    modes = {
        'sample': InterleaveMode.SAMPLE,
        'line': InterleaveMode.LINE,
        'none': InterleaveMode.NONE
    }
    return modes[mode]


class JplsImageEncoder:
    def __init__(self):
        self._charls = _load_charls()
        self._charls.charls_jpegls_encoder_create.restype = c_void_p
        self._encoder = c_void_p(self._charls.charls_jpegls_encoder_create())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def call_charls_encode(self, fn, *args):
        err = fn(self._encoder, *args)
        if err != CharlsErrorCode.SUCCESS:
            raise CharlsError(CharlsErrorCode(err))

    def _estimate_encoded_size(self):
        encoded_buffer_size = c_size_t(0)
        error = self._charls.charls_jpegls_encoder_get_estimated_destination_size(
            self._encoder,
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
        frame_info = FrameInfo(im.width, im.height, bits_per_component, components)
        error = self._charls.charls_jpegls_encoder_set_frame_info(self._encoder, pointer(frame_info))

        if components > 1:
            interleave_mode = _line_interleave_mode(im.encoderinfo.get('interleave_mode', 'sample'))
            self.call_charls_encode(self._charls.charls_jpegls_encoder_set_interleave_mode, interleave_mode)
        else:
            interleave_mode = InterleaveMode.NONE

        encoded_size = self._estimate_encoded_size()
        encoded_buffer = bytearray(encoded_size)
        encoded_buffer_type = c_uint8 * encoded_size

        error = self._charls.charls_jpegls_encoder_set_destination_buffer(
            self._encoder,
            encoded_buffer_type.from_buffer(encoded_buffer),
            encoded_size
        )

        if im.encoderinfo.get('spiff', True):
            error = self._charls.charls_jpegls_encoder_write_standard_spiff_header(
                self._encoder,
                c_int32(SpiffColorSpace.GRAYSCALE),
                c_int32(SpiffResolutionUnits.DOTS_PER_INCH.value),
                72,
                72
            )

        data = _pixel_data_for_encoding(im, bits_per_component, components, interleave_mode)
        error = self._charls.charls_jpegls_encoder_encode_from_buffer(
            self._encoder,
            pointer(data),
            len(data),
            0
        )
        bytes_written = c_size_t(0)
        error = self._charls.charls_jpegls_encoder_get_bytes_written(
            self._encoder,
            pointer(bytes_written)
        )

        encoded_bytes = bytes_written.value

        fp.write(encoded_buffer[:encoded_bytes])

    def cleanup(self):
        self._charls.charls_jpegls_encoder_destroy(self._encoder)
