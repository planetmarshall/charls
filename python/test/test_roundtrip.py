from os import path
from io import BytesIO

from PIL import Image
import pytest

import jpls_image_plugin

@pytest.mark.parametrize("source_image, encoded_image, kwargs",[
    ("TEST16.PGM", "T16E0.JLS", {'spiff': False, 'bits_per_component': 12}),
    ("TEST8.PPM", "T8C0E0.JLS", {'spiff': False})
])
def test_encode(conformance, source_image, encoded_image, kwargs):
    src = path.abspath(path.join(conformance, source_image))
    src_image = Image.open(src)
    stream = BytesIO()
    src_image.save(stream, "JPEG-LS", **kwargs)
    encoded_data = stream.getvalue()

    with open(path.join(conformance, encoded_image), 'rb') as fp:
        expected_encoded_data = fp.read()

    assert len(expected_encoded_data) == len(encoded_data)
    assert expected_encoded_data == encoded_data


# def test_roundtrip():
#     test_conformance = path.join('../test/conformance')
#     test_16 = path.abspath(path.join(test_conformance, 'TEST16.PGM'))
#     src_image = Image.open(test_16)
#     src_pixels = list(src_image.getdata())
#
#     stream = BytesIO()
#     src_image.save(stream, "JPEG-LS")
#     stream.seek(0)
#     dest_image = Image.open(stream)
#
#     dest_pixels = list(dest_image.getdata())
#
#     assert src_pixels == dest_pixels