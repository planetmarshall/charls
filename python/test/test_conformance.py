from os import path
from io import BytesIO

from PIL import Image
import pytest

from charls import init_pillow_plugin

init_pillow_plugin()


@pytest.mark.parametrize("source_image, encoded_image, kwargs",[
    ("TEST16.PGM", "T16E0.JLS", {'spiff': False, 'bits_per_component': 12}),
    ("TEST8.PPM", "T8C0E0.JLS", {'spiff': False, 'interleave_mode': 'none'}),
    ("TEST8.PPM", "T8C1E0.JLS", {'spiff': False, 'interleave_mode': 'line'}),
    ("TEST8.PPM", "T8C2E0.JLS", {'spiff': False })
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


@pytest.mark.parametrize("encoded_image, decoded_image", [
    ("T16E0.JLS", "TEST16.PGM"),
    ("T8C0E0.JLS", "TEST8.PPM"),
    ("T8C1E0.JLS", "TEST8.PPM"),
    ("T8C2E0.JLS", "TEST8.PPM")
])
def test_decode(conformance, encoded_image, decoded_image):
    src = path.abspath(path.join(conformance, encoded_image))
    src_image = Image.open(src)

    dest = path.abspath(path.join(conformance, decoded_image))
    expected_image = Image.open(dest)

    src_data = list(src_image.getdata())
    expected_data = list(expected_image.getdata())

    assert len(expected_data) == len(src_data)
    assert expected_data == src_data
