import struct

from PIL import Image, ImageFile
from .JplsImageCodec import JplsImageEncoder


def _spiff(header):
    magic_number = header[:4]
    compression = header[26]
    if not (magic_number == b"\xff\xd8\xff\xe8" and compression == 6):
        raise SyntaxError("Not a JPEG-LS encoded SPIFF file")

    return {
        "header_length": struct.unpack_from(">H", header, 4)[0],
        "version": struct.unpack_from(">BB", header, 12),
        "profile_id": header[14],
        "number_of_components": header[15],
        "height": struct.unpack_from(">I", header, 16)[0],
        "width": struct.unpack_from(">I", header, 20)[0],
        "color_space_id": header[24],
        "bits_per_sample": header[25]
    }


def _save(im, fp, filename):
    encoder = JplsImageEncoder()
    encoder.encode(im, fp)


class JplsImageFile(ImageFile.ImageFile):

    format = "JPEG-LS"
    format_description = "JPEG-LS compressed raster image"
    _mode_map = {
        (1, 8) : "L",
        (3, 8) : "RGB",
        (1, 16): "I;16",
        (3, 16): "RGB;16"
    }

    def _open(self):
        spiff = _spiff(self.fp.read(32))

        self._size = (spiff["width"], spiff["height"])
        mode_key = (spiff["number_of_components"], spiff["bits_per_sample"])
        self.mode = self._mode_map.get(mode_key)
        if self.mode is None:
            raise SyntaxError("Mode not supported (Number of components: {}, Bits per sample: {})".format(*mode_key))
        self.tile = [
            ("jpeg_ls", (0, 0) + self.size, 0, (self.mode, 0))
        ]


