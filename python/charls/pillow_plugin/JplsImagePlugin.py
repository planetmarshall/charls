import struct

from PIL import ImageFile
from charls.pillow_plugin.JplsImageCodec import JplsImageEncoder


def _accept(header):
    magic_number = header[:4]
    return magic_number == b"\xff\xd8\xff\xe8" or magic_number == b"\xff\xd8\xff\xf7"


def _spiff(header):
    magic_number = header[:4]
    compression = header[26]
    if not (magic_number == b"\xff\xd8\xff\xe8" and compression == 6):
        return None

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


def _jpegls_marker(header):
    magic_number = header[:4]
    if not magic_number == b"\xff\xd8\xff\xf7":
        return None

    return {
        "bits_per_sample": header[6],
        "height": struct.unpack_from(">H", header, 7)[0],
        "width": struct.unpack_from(">H", header, 9)[0],
        "number_of_components": header[11]
    }


def _save(im, fp, filename):
    with JplsImageEncoder() as encoder:
        encoder.encode(im, fp)


class JplsImageFile(ImageFile.ImageFile):

    format = "JPEG-LS"
    format_description = "JPEG-LS compressed raster image"
    _mode_map = {
        (1, 8): "L",
        (3, 8): "RGB",
        (1, 16): "I;16",
        (3, 16): "RGB;16"
    }

    def _open(self):
        header = self.fp.read(32)
        meta = _spiff(header) or _jpegls_marker(header)
        if not meta:
            raise SyntaxError("Not a JPEG-LS file")

        self._size = (meta["width"], meta["height"])
        bits_per_sample = meta["bits_per_sample"] if meta["bits_per_sample"] <= 8 else 16
        mode_key = (meta["number_of_components"], bits_per_sample)
        self.mode = self._mode_map.get(mode_key)
        if self.mode is None:
            raise IOError("Mode not supported (Number of components: {}, Bits per sample: {})".format(*mode_key))
        self.tile = [
            ("jpeg_ls", (0, 0) + self.size, 0, (self.mode, 0))
        ]


